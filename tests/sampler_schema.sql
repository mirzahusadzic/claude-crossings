-- The three tables of the store's index the adapter reads. Nothing else of the store is needed here.
create table said(seq integer primary key, uuid text unique, id text, session text, voice text, at text,
                  text text, model text);
create index said_id on said(id);
create table label(n integer primary key, id text unique, kind text, whose text, text text, page text,
                   parent text, home text, state text, model text);
create table anchor(label text, said text);
create index anchor_said on anchor(said);
create index anchor_label on anchor(label);
