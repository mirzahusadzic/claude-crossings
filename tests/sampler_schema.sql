-- The three tables of the store's index the adapter reads. Nothing else of the store is needed here.
create table said(seq integer primary key, uuid text unique, id text, session text, voice text, at text,
                  text text, model text);
create index said_id on said(id);
create table label(n integer primary key, id text unique, kind text, whose text, text text, page text,
                   parent text, home text, state text, model text);
create table anchor(label text, said text, uuid text, gone integer);
create index anchor_said on anchor(said);
create index anchor_label on anchor(label);
-- What a build keeps with an anchor whose id one message holds: that message's whole id (see store._rested).
create trigger anchor_rests after insert on anchor when new.uuid is null and (select count(*) from said where id = new.said) = 1
begin update anchor set uuid = (select uuid from said where id = new.said), gone = 0 where rowid = new.rowid; end;
