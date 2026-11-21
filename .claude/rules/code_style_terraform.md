---
paths:
  - 'terraform/**'
---

# Rules: Terraform code style

How the `.tf` files in `terraform/` are laid out, named and written. The architecture, version, safety and check rules are in `engineer_cloud.md`.

<br>

## Folders

```text
terraform/
├── environments/
│   └── <env>/                       # where and with which values
│       ├── .terraform.lock.hcl      # committed
│       ├── backend.hcl.example
│       ├── backend.tf
│       ├── main.tf
│       ├── outputs.tf
│       ├── terraform.tfvars.example
│       ├── variables.tf
│       └── versions.tf
└── modules/
    └── <app>/                       # what to build: the resources
        ├── outputs.tf
        ├── registry.tf              # one file per concern: sql.tf, run.tf, ...
        ├── tests/                   # <concern>.tftest.hcl
        ├── variables.tf
        └── versions.tf
```

- **Resources** go in the module. **State, provider and values** go in the environment.

<br>

## Files

| File               | Holds                                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **`versions.tf`**  | `terraform { required_version, required_providers }`; not `terraform.tf`                                           |
| **`backend.tf`**   | `terraform { backend "gcs" { prefix = "..." } }`; the environment only                                             |
| **`main.tf`**      | The `provider` block and, in an environment, the module call; `providers.tf` only for several providers or aliases |
| **`variables.tf`** | Every `variable`, alphabetical                                                                                     |
| **`outputs.tf`**   | Every `output`, alphabetical                                                                                       |
| **`<concern>.tf`** | The resources of one concern; no `main.tf` in a module unless shared resources need one                            |
| **`locals.tf`**    | Only when several files use the same `locals`; otherwise at the top of the file                                    |
| **`README.md`**    | In a module, only when it is useful: inputs, outputs, an example call                                              |

- **File names:** lowercase, words separated by underscores.

<br>

## Names

| Name                                 | Rule                                                  | Example                                     |
| ------------------------------------ | ----------------------------------------------------- | ------------------------------------------- |
| **Resource name** (second label)     | A noun, underscores, never the resource type again    | `google_sql_database.app`                   |
| **Variable, output, module**         | Nouns, underscores; the module folder and label match | `project_id`, `content_hub`                 |
| **Cloud name** (the `name` argument) | GCP's rules: lowercase, hyphens, the app as prefix    | `content-hub-app`                           |
| **Name GCP blocks after deletion**   | Add a `random_id` suffix                              | `content-hub-db-${random_id.db_suffix.hex}` |

<br>

## Order inside a block

```hcl
resource "google_cloud_run_v2_service" "app" {
  count = 1                  # 1. count or for_each (only if needed)

  name     = "content-hub"   # 2. arguments, = aligned by terraform fmt
  location = var.region

  template { ... }           # 3. nested blocks

  lifecycle { ... }          # 4. lifecycle (only if needed)

  depends_on = [...]         # 5. depends_on, last
}
```

- **One blank line** between the groups.
- **`variable`:** `type`, `description`, `default`, `sensitive`, `validation`.
- **`output`:** `description`, `value`, `sensitive`.
- **References, not repeated strings:** `google_sql_database_instance.main.name`, never the same name written twice.
- **Comments:** `#` only; one or two lines, only the reason.
- **Formatting:** `terraform fmt` decides; never align by hand.

<br>

## Variables and outputs

- **Every variable:** `type` and `description`. **Every output:** `description`.
- **Defaults:** none in the module. In the environment, only for its own choices, such as `region`.
- **Few inputs:** only what really changes between deployments.
- **Secrets:** never in a variable or `.tfvars`; generate them (`random_password`). An output that holds a secret gets `sensitive = true`.
- **`validation` blocks:** only for an unusual restriction.
- **Outputs passed on:** the environment repeats the module outputs the maintainer needs on the command line.
