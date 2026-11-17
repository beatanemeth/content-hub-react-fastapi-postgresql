-- The server reads the files from /seed, the folder that docker-compose.yaml mounts from ./db/seed.
-- HEADER MATCH stops with an error if a CSV header differs from the table's column names.
-- Order: a parent table is loaded before any table that references it.

COPY person FROM '/seed/person.csv' WITH (FORMAT csv, HEADER MATCH);
COPY venue FROM '/seed/venue.csv' WITH (FORMAT csv, HEADER MATCH);
COPY category FROM '/seed/category.csv' WITH (FORMAT csv, HEADER MATCH);
COPY event_category FROM '/seed/event_category.csv' WITH (FORMAT csv, HEADER MATCH);
COPY tag FROM '/seed/tag.csv' WITH (FORMAT csv, HEADER MATCH);

COPY staff FROM '/seed/staff.csv' WITH (FORMAT csv, HEADER MATCH);
COPY founder FROM '/seed/founder.csv' WITH (FORMAT csv, HEADER MATCH);

COPY post FROM '/seed/post.csv' WITH (FORMAT csv, HEADER MATCH);
COPY post_category FROM '/seed/post_category.csv' WITH (FORMAT csv, HEADER MATCH);
COPY post_tag FROM '/seed/post_tag.csv' WITH (FORMAT csv, HEADER MATCH);

COPY event FROM '/seed/event.csv' WITH (FORMAT csv, HEADER MATCH);
COPY event_speaker FROM '/seed/event_speaker.csv' WITH (FORMAT csv, HEADER MATCH);

-- COPY wrote the ids itself, so each identity counter is still at 1.
-- setval moves it to the highest id, so the next INSERT gets max + 1.
SELECT setval(pg_get_serial_sequence('person', 'id'), (SELECT max(id) FROM person));
SELECT setval(pg_get_serial_sequence('venue', 'id'), (SELECT max(id) FROM venue));
SELECT setval(pg_get_serial_sequence('category', 'id'), (SELECT max(id) FROM category));
SELECT setval(pg_get_serial_sequence('event_category', 'id'), (SELECT max(id) FROM event_category));
SELECT setval(pg_get_serial_sequence('tag', 'id'), (SELECT max(id) FROM tag));
SELECT setval(pg_get_serial_sequence('post', 'id'), (SELECT max(id) FROM post));
SELECT setval(pg_get_serial_sequence('event', 'id'), (SELECT max(id) FROM event));
