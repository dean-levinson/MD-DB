# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: mdlib/md.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0emdlib/md.proto\x12\tprotoblog\"k\n\x08\x44\x42\x41\x63tion\x12\'\n\x0b\x61\x63tion_type\x18\x01 \x01(\x0e\x32\x12.protoblog.Actions\x12\x10\n\x03key\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x12\n\x05value\x18\x03 \x01(\tH\x01\x88\x01\x01\x42\x06\n\x04_keyB\x08\n\x06_value\",\n\x06\x44\x42Info\x12\x0f\n\x07\x64\x62_name\x18\x01 \x01(\t\x12\x11\n\tclient_id\x18\x02 \x01(\x05\"\x18\n\x05GetDB\x12\x0f\n\x07\x64\x62_file\x18\x01 \x01(\x0c\"\x1c\n\tGetDBHash\x12\x0f\n\x07\x64\x62_hash\x18\x01 \x01(\t\"/\n\nGetDBState\x12!\n\x05state\x18\x01 \x01(\x0e\x32\x12.protoblog.DBState*j\n\x07\x41\x63tions\x12\x0c\n\x08\x41\x44\x44_ITEM\x10\x00\x12\r\n\tSET_VALUE\x10\x01\x12\x11\n\rGET_KEY_VALUE\x10\x02\x12\x10\n\x0cGET_ALL_KEYS\x10\x03\x12\x0e\n\nDELETE_KEY\x10\x04\x12\r\n\tDELETE_DB\x10\x05*%\n\x07\x44\x42State\x12\x0e\n\nNOT_SYNCED\x10\x00\x12\n\n\x06SYNCED\x10\x01\x62\x06proto3')

_ACTIONS = DESCRIPTOR.enum_types_by_name['Actions']
Actions = enum_type_wrapper.EnumTypeWrapper(_ACTIONS)
_DBSTATE = DESCRIPTOR.enum_types_by_name['DBState']
DBState = enum_type_wrapper.EnumTypeWrapper(_DBSTATE)
ADD_ITEM = 0
SET_VALUE = 1
GET_KEY_VALUE = 2
GET_ALL_KEYS = 3
DELETE_KEY = 4
DELETE_DB = 5
NOT_SYNCED = 0
SYNCED = 1


_DBACTION = DESCRIPTOR.message_types_by_name['DBAction']
_DBINFO = DESCRIPTOR.message_types_by_name['DBInfo']
_GETDB = DESCRIPTOR.message_types_by_name['GetDB']
_GETDBHASH = DESCRIPTOR.message_types_by_name['GetDBHash']
_GETDBSTATE = DESCRIPTOR.message_types_by_name['GetDBState']
DBAction = _reflection.GeneratedProtocolMessageType('DBAction', (_message.Message,), {
  'DESCRIPTOR' : _DBACTION,
  '__module__' : 'mdlib.md_pb2'
  # @@protoc_insertion_point(class_scope:protoblog.DBAction)
  })
_sym_db.RegisterMessage(DBAction)

DBInfo = _reflection.GeneratedProtocolMessageType('DBInfo', (_message.Message,), {
  'DESCRIPTOR' : _DBINFO,
  '__module__' : 'mdlib.md_pb2'
  # @@protoc_insertion_point(class_scope:protoblog.DBInfo)
  })
_sym_db.RegisterMessage(DBInfo)

GetDB = _reflection.GeneratedProtocolMessageType('GetDB', (_message.Message,), {
  'DESCRIPTOR' : _GETDB,
  '__module__' : 'mdlib.md_pb2'
  # @@protoc_insertion_point(class_scope:protoblog.GetDB)
  })
_sym_db.RegisterMessage(GetDB)

GetDBHash = _reflection.GeneratedProtocolMessageType('GetDBHash', (_message.Message,), {
  'DESCRIPTOR' : _GETDBHASH,
  '__module__' : 'mdlib.md_pb2'
  # @@protoc_insertion_point(class_scope:protoblog.GetDBHash)
  })
_sym_db.RegisterMessage(GetDBHash)

GetDBState = _reflection.GeneratedProtocolMessageType('GetDBState', (_message.Message,), {
  'DESCRIPTOR' : _GETDBSTATE,
  '__module__' : 'mdlib.md_pb2'
  # @@protoc_insertion_point(class_scope:protoblog.GetDBState)
  })
_sym_db.RegisterMessage(GetDBState)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ACTIONS._serialized_start=289
  _ACTIONS._serialized_end=395
  _DBSTATE._serialized_start=397
  _DBSTATE._serialized_end=434
  _DBACTION._serialized_start=29
  _DBACTION._serialized_end=136
  _DBINFO._serialized_start=138
  _DBINFO._serialized_end=182
  _GETDB._serialized_start=184
  _GETDB._serialized_end=208
  _GETDBHASH._serialized_start=210
  _GETDBHASH._serialized_end=238
  _GETDBSTATE._serialized_start=240
  _GETDBSTATE._serialized_end=287
# @@protoc_insertion_point(module_scope)
