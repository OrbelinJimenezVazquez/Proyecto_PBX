from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, BigInteger
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

# Modelo para Queue Log (asteriskcdrdb) - Estructura REAL
class QueueLog(Base):
    __tablename__ = "queuelog"
    __table_args__ = {'schema': 'asteriskcdrdb'}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    time = Column(DateTime, index=True)
    callid = Column(String(40), index=True)
    queuename = Column(String(20), index=True)
    serverid = Column(String(20))
    agent = Column(String(40), index=True)
    event = Column(String(20), index=True)
    data1 = Column(String(40))
    data2 = Column(String(40))
    data3 = Column(String(40))
    data4 = Column(String(40))
    data5 = Column(String(40))

# Modelo para Queue Stats (qstats) - Estructura REAL
class QueueStats(Base):
    __tablename__ = "queue_stats"
    __table_args__ = {'schema': 'qstats'}
    
    queue_stats_id = Column(Integer, primary_key=True)
    uniqued = Column(String(40))
    datetime = Column(DateTime, index=True)
    gname = Column(Integer)
    qqsent = Column(Integer)
    gevent = Column(Integer)
    info1 = Column(String(50))
    info2 = Column(String(50))
    info3 = Column(String(50))
    info4 = Column(String(50))
    info5 = Column(String(50))

# Modelo para Queue Stats MV (vista materializada - qstats) - Estructura REAL
class QueueStatsMV(Base):
    __tablename__ = "queue_stats_mv"
    __table_args__ = {'schema': 'qstats'}
    
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, index=True)
    datetimeconnect = Column(DateTime)
    datetimeend = Column(DateTime)
    queue = Column(String(100), index=True)
    agent = Column(String(100))
    event = Column(String(40), index=True)
    uniqueid = Column(String(50))
    real_uniqueid = Column(String(50))
    did = Column(String(100))
    url = Column(String(100))
    position = Column(Integer)
    info1 = Column(String(50))
    info2 = Column(String(50))
    info3 = Column(String(50))
    info4 = Column(String(50))
    info5 = Column(String(50))
    overflow = Column(Integer)
    combined_waittime = Column(Integer)
    waittime = Column(Integer)
    talktime = Column(Integer)
    ringtime = Column(Integer)

# Modelo para Agent Activity (qstats) - Monitor de agentes en tiempo real
class AgentActivity(Base):
    __tablename__ = "agent_activity"
    __table_args__ = {'schema': 'qstats'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, index=True)
    queue = Column(Text)
    agent = Column(String(100), index=True)
    event = Column(String(40), index=True)
    data = Column(String(150))
    lastedforseconds = Column(Integer)
    uniqueid = Column(String(100), index=True)
    computed = Column(Integer)
    info1 = Column(String(200))
    info2 = Column(String(200))

# Modelo para Agent Activity Pause (qstats) - Pausas de agentes
class AgentActivityPause(Base):
    __tablename__ = "agent_activity_pause"
    __table_args__ = {'schema': 'qstats'}
    
    agent = Column(String(250), primary_key=True)
    datetime = Column(DateTime)
    state = Column(String(15))
    queue = Column(String(250))
    data = Column(String(150))
    computed = Column(Integer)
    pauseid = Column(Integer)

# Modelo para Agent Activity Session (qstats) - Sesiones login/logout
class AgentActivitySession(Base):
    __tablename__ = "agent_activity_session"
    __table_args__ = {'schema': 'qstats'}
    
    agent = Column(String(250), primary_key=True)
    datetime = Column(DateTime)
    state = Column(String(15))
    queue = Column(String(250))
    data = Column(String(150))
    incall = Column(Integer)
    sessionid = Column(Integer)
    sessioncount = Column(Integer)
    computed = Column(Integer)

# Modelo para AgentNames (qstats) - Catálogo de agentes
class AgentName(Base):
    __tablename__ = "agentnames"
    __table_args__ = {'schema': 'qstats'}
    
    id = Column(Integer, primary_key=True)
    qagent = Column(Integer, index=True)
    agent = Column(String(250), index=True)
    name = Column(String(250))

# Modelo para Pauses (qstats) - Catálogo de tipos de pausa
class Pause(Base):
    __tablename__ = "pauses"
    __table_args__ = {'schema': 'qstats'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    color = Column(String(15))

# Modelo para QueueNames (qstats) - Nombres de colas
class QueueName(Base):
    __tablename__ = "queuenames"
    __table_args__ = {'schema': 'qstats'}
    
    id = Column(Integer, primary_key=True)
    qname = Column(Integer, index=True)
    queue = Column(String(250), index=True)
    descr = Column(String(250))
