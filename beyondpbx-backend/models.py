from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# Modelo para CDR (Call Detail Records)
class CDR(Base):
    __tablename__ = "cdr"
    __table_args__ = {'schema': 'asteriskcdrdb'}
    
    id = Column(Integer, primary_key=True, index=True)
    src = Column(String(80))
    dst = Column(String(80))
    calldate = Column(DateTime, index=True)
    duration = Column(Integer)
    billsec = Column(Integer)
    disposition = Column(String(45), index=True)
    uniqueid = Column(String(150))
    recordingfile = Column(String(255))
    did = Column(String(50))

# Modelo para Users (extensiones)
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'asterisk'}
    
    extension = Column(String(50), primary_key=True)
    name = Column(String(50))
    
# Modelo para SIP (configuración de extensiones SIP)
class SIP(Base):
    __tablename__ = "sip"
    __table_args__ = {'schema': 'asterisk'}
    
    id = Column(String(50), primary_key=True)
    keyword = Column(String(50), primary_key=True)
    data = Column(String(255))
    flags = Column(Integer, default=0)

# Modelo para Trunks (troncales)
class Trunk(Base):
    __tablename__ = "trunks"
    __table_args__ = {'schema': 'asterisk'}
    
    trunkid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    tech = Column(String(20))
    channelid = Column(String(50))
    disabled = Column(String(1))

# Modelo para IVR Details (IVRs) - Solo columnas que existen en la tabla real
class IVRDetail(Base):
    __tablename__ = "ivr_details"
    __table_args__ = {'schema': 'asterisk'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    description = Column(String(255))
    announcement = Column(Integer)
    directdial = Column(String(50))
    invalid_loops = Column(Integer)
    invalid_retry_recording = Column(Integer)
    invalid_recording = Column(Integer)
    retvm = Column(String(8))
    timeout_time = Column(Integer)
    timeout_recording = Column(Integer)
    timeout_retry_recording = Column(Integer)
    timeout_ivr_ret = Column(Integer)
    timeout_loops = Column(Integer)
    timeout_append_announce = Column(Integer)
    invalid_append_announce = Column(Integer)
    invalid_ivr_ret = Column(Integer)

# Modelo para IVR Entries (opciones de IVR)
class IVREntry(Base):
    __tablename__ = "ivr_entries"
    __table_args__ = {'schema': 'asterisk'}
    
    ivr_id = Column(Integer, primary_key=True)
    selection = Column(String(30), primary_key=True)  # Cambiado de String(1) a String(30)
    dest = Column(String(255))
    ivr_ret = Column(Integer)

# Modelo para Incoming Routes (rutas entrantes)
class IncomingRoute(Base):
    __tablename__ = "incoming"
    __table_args__ = {'schema': 'asterisk'}
    
    cidnum = Column(String(50), primary_key=True)
    extension = Column(String(50))
    destination = Column(String(255))
    description = Column(String(255))
    alertinfo = Column(String(255))
    mohclass = Column(String(80))
    ringing = Column(String(80))
    delay_answer = Column(Integer)
    pricid = Column(Integer)
    rvolume = Column(String(5))