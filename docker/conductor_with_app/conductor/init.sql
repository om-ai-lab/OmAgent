CREATE DATABASE IF NOT EXISTS om_app_agent;
use om_app_agent;
create table tbl_chat_record
(
    id            bigint auto_increment comment 'main key'
        primary key,
    creator_id    bigint           not null comment 'creator id',
    create_time   datetime         null comment 'creation time',
    update_id     bigint           null comment 'updater id',
    update_time   datetime         null comment 'update time',
    deleted       int(2) default 0 not null comment '0.not deleted  other.deleted',
    remark        varchar(512)     null comment 'remark',
    user_id       varchar(64)      null comment 'reserved, user main key id',
    session_id    varchar(64)      null comment 'sessionid for a complete conversation',
    content       json             null comment 'content',
    type          int    default 1 not null comment 'message type, 1: normal, 2: reserved, 3: time series',
    role          varchar(16)      null comment 'role, user, assistant, system',
    workflow_name varchar(512)     null comment 'workflow name',
    content_status varchar(64)     null comment 'answer status'

)
    comment 'chat record table';

create table tbl_workflow_record
(
    id            bigint auto_increment comment 'main key'
        primary key,
    creator_id    bigint           not null comment 'creator id',
    create_time   datetime         null comment 'creation time',
    update_id     bigint           null comment 'updater id',
    update_time   datetime         null comment 'update time',
    deleted       int(2) default 0 not null comment '0.not deleted  other.deleted',
    remark        varchar(512)     null comment 'remark',
    user_id       varchar(64)      null comment 'reserved, user main key id',
    session_id    varchar(64)      null comment 'sessionid for a complete conversation',
    progress      varchar(512)     null comment 'progress',
    message       varchar(512)     null comment 'progress message',
    workflow_name varchar(512)     null comment 'workflow name'

)
    comment 'workflow running record table';

create table tbl_resource
(
    id            bigint auto_increment comment 'main key'
        primary key,
    creator_id    bigint           not null comment 'creator id',
    create_time   datetime         null comment 'creation time',
    update_id     bigint           null comment 'updater id',
    update_time   datetime         null comment 'update time',
    deleted       int(2) default 0 not null comment '0.not deleted  other.deleted',
    remark        varchar(512)     null comment 'remark',
    user_id       varchar(64)      null comment 'reserved, user main key id',
    resource_id   varchar(64)      null comment 'resource unique identifier',
    type          int(4) default 1 null comment 'resource type, 1: image',
    resource_url  varchar(512)     null comment 'resource url',
    resource_name varchar(512)     null comment 'resource name',
    preview_url   varchar(512)     null comment 'reserved, preview url',
    resource_key  varchar(512)     null comment 'object storage key'
) comment 'resource table';

create table tbl_dictionary
(
    id              int auto_increment comment '主键'
        primary key,
    type            varchar(255)                       null comment 'enum value',
    type_name       varchar(255)                       null comment 'type description',
    name            varchar(255)                       null comment 'enum name',
    value           int                                null comment 'type',
    pid             int                                null comment 'parent node',
    sort            int(16)                            null comment 'sort',
    create_time     datetime default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    update_time     datetime default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    deleted         tinyint  default 0                 null comment '0.not deleted  other.deleted',
    extension_value varchar(100)                       null comment 'extra value'
)
    comment 'dictionary table';

INSERT INTO tbl_dictionary (id, type, type_name, name, value, pid, sort, create_time, update_time, deleted,
                            extension_value)
VALUES (1, 'chat_turns', 'turns of single chat conversation', '5', 1, null, 1, null, null, 0, null);

CREATE USER 'hd'@'%' IDENTIFIED WITH mysql_native_password BY 'F098058455ec50b3a';
GRANT ALL PRIVILEGES ON om_app_agent.* TO 'hd'@'%';
FLUSH PRIVILEGES;
