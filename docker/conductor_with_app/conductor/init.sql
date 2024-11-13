CREATE DATABASE IF NOT EXISTS om_app_agent;
use om_app_agent;
create table tbl_chat_record
(
    id            bigint auto_increment comment '主键id'
        primary key,
    creator_id    bigint           not null comment '创建者id',
    create_time   datetime         null comment '创建时间',
    update_id     bigint           null comment '更新者id',
    update_time   datetime         null comment '更新时间',
    deleted       int(2) default 0 not null comment '0.未删除 其他.已删除',
    remark        varchar(512)     null comment '备注',
    user_id       varchar(64)      null comment '预留，用户主键id',
    session_id    varchar(64)      null comment 'sessionid 一次完整会话标识',
    content       json             null comment '内容',
    type          int    default 1 not null comment '消息类型，1：普通，2，预留，3：时序',
    role          varchar(16)      null comment '角色user, assistant,system',
    workflow_name varchar(512)     null comment 'workflow名称',
    content_status varchar(64)     null comment '回答状态'

)
    comment '聊天记录表';

create table tbl_workflow_record
(
    id            bigint auto_increment comment '主键id'
        primary key,
    creator_id    bigint           not null comment '创建者id',
    create_time   datetime         null comment '创建时间',
    update_id     bigint           null comment '更新者id',
    update_time   datetime         null comment '更新时间',
    deleted       int(2) default 0 not null comment '0.未删除 其他.已删除',
    remark        varchar(512)     null comment '备注',
    user_id       varchar(64)      null comment '预留，用户主键id',
    session_id    varchar(64)      null comment 'sessionid 一次完整会话标识',
    progress      varchar(512)     null comment '运行进度',
    message       varchar(512)     null comment '运行进度说明',
    workflow_name varchar(512)     null comment 'workflow名称'

)
    comment 'workflow运行记录表';

create table tbl_resource
(
    id            bigint auto_increment comment '主键id'
        primary key,
    creator_id    bigint           not null comment '创建者id',
    create_time   datetime         null comment '创建时间',
    update_id     bigint           null comment '更新者id',
    update_time   datetime         null comment '更新时间',
    deleted       int(2) default 0 not null comment '0.未删除 其他.已删除',
    remark        varchar(512)     null comment '备注',
    user_id       varchar(64)      null comment '预留，用户主键id',
    resource_id   varchar(64)      null comment '资源唯一标识',
    type          int(4) default 1 null comment '资源类型，1：图片',
    resource_url  varchar(512)     null comment '资源url',
    resource_name varchar(512)     null comment '资源名称',
    preview_url   varchar(512)     null comment '预留，预览url',
    resource_key  varchar(512)     null comment '对象存储key'
) comment '资源表';

create table tbl_dictionary
(
    id              int auto_increment comment '主键'
        primary key,
    type            varchar(255)                       null comment '枚举值',
    type_name       varchar(255)                       null comment '类型描述',
    name            varchar(255)                       null comment '枚举名称',
    value           int                                null comment '类型',
    pid             int                                null comment '父节点',
    sort            int(16)                            null comment '排序',
    create_time     datetime default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    update_time     datetime default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    deleted         tinyint  default 0                 null comment '是否删除  1：已删除  0：未删除',
    extension_value varchar(100)                       null comment '额外值'
)
    comment '字典表';

INSERT INTO tbl_dictionary (id, type, type_name, name, value, pid, sort, create_time, update_time, deleted,
                            extension_value)
VALUES (1, 'chat_turns', 'turns of single chat conversation', '5', 1, null, 1, null, null, 0, null);

CREATE USER 'hd'@'%' IDENTIFIED WITH mysql_native_password BY 'F098058455ec50b3a';
GRANT ALL PRIVILEGES ON om_app_agent.* TO 'hd'@'%';
FLUSH PRIVILEGES;
