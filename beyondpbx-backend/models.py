from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, BigInteger, TIMESTAMP
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
    datetime = Column(TIMESTAMP, nullable=False)
    state = Column(String(15))
    queue = Column(String(250))
    data = Column(String(150))
    computed = Column(Integer)
    pauseid = Column(Integer)
    
    def __repr__(self):
        return f"<AgentActivityPause(agent={self.agent}, state={self.state})>"

# Modelo para Agent Activity Defer Pause (qstats) - Pausas diferidas
class AgentActivityDeferPause(Base):
    __tablename__ = "agent_activity_deferpause"
    __table_args__ = {'schema': 'qstats'}
    
    agent = Column(String(250), primary_key=True)
    reason = Column(String(250))
    datetime = Column(TIMESTAMP, nullable=False)
    
    def __repr__(self):
        return f"<AgentActivityDeferPause(agent={self.agent}, reason={self.reason})>"

# Modelo para Agent Activity Session (qstats) - Sesiones login/logout
class AgentActivitySession(Base):
    __tablename__ = "agent_activity_session"
    __table_args__ = {'schema': 'qstats'}
    
    agent = Column(String(250), primary_key=True)
    datetime = Column(TIMESTAMP, nullable=False)
    state = Column(String(15))
    queue = Column(String(250))
    data = Column(String(150))
    incall = Column(Integer)
    sessionid = Column(Integer)
    sessioncount = Column(Integer)
    computed = Column(Integer)
    
    def __repr__(self):
        return f"<AgentActivitySession(agent={self.agent}, state={self.state})>"

# Modelo para AgentNames (qstats) - Catálogo de agentes
class AgentName(Base):
    __tablename__ = "agentnames"
    __table_args__ = {'schema': 'qstats'}
    
    device = Column(String(50), primary_key=True)
    agent = Column(String(255), nullable=True)

# Modelo para Pauses (qstats) - Catálogo de tipos de pausa
class Pause(Base):
    __tablename__ = "pauses"
    __table_args__ = {'schema': 'qstats'}
    
    pause_id = Column(String(50), primary_key=True)
    pause_name = Column(String(100), nullable=False)
    
    def __repr__(self):
        return f"<Pause(pause_id={self.pause_id}, pause_name={self.pause_name})>"

# Modelo para QueueNames (qstats) - Nombres de colas
class QueueName(Base):
    __tablename__ = "queuenames"
    __table_args__ = {'schema': 'qstats'}
    
    device = Column(String(50), primary_key=True)  # PK según la estructura
    queue = Column(String(255), nullable=True)  # Permite NULL según tu estructura
    
    def __repr__(self):
        return f"<QueueName(device={self.device}, queue={self.queue})>"
    
#Modelo para QEvent (qstats) - Catálogo de eventos
class QEvent(Base):
    __tablename__ = "qevent"
    __table_args__ = {'schema': 'qstats'}
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    event = Column(String(40), nullable=True)
    
    def __repr__(self):
        return f"<QEvent(event_id={self.event_id}, event={self.event})>"

# Modelo para QAgent (qstats) - Catálogo de agentes con ID numérico
class QAgent(Base):
    __tablename__ = "qagent"
    __table_args__ = {'schema': 'qstats'}
    
    agent_id = Column(Integer, primary_key=True, autoincrement=True)
    agent = Column(String(100))
    disabled = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<QAgent(agent_id={self.agent_id}, agent={self.agent})>"

# Modelo para QName (qstats) - Catálogo de colas con ID numérico
class QName(Base):
    __tablename__ = "qname"
    __table_args__ = {'schema': 'qstats'}
    
    queue_id = Column(Integer, primary_key=True, autoincrement=True)
    queue = Column(String(40), nullable=False)
    
    def __repr__(self):
        return f"<QName(queue_id={self.queue_id}, queue={self.queue})>"

# Modelo para SQLRealtime (qstats) - Configuración realtime
class SQLRealtime(Base):
    __tablename__ = "sqlrealtime"
    __table_args__ = {'schema': 'qstats'}
    
    user = Column(String(100), primary_key=True)
    lastupdate = Column(TIMESTAMP, nullable=False)
    data = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SQLRealtime(user={self.user}, lastupdate={self.lastupdate})>"

# Modelo para Queues (asterisk) - Definición de colas
class Queue(Base):
    __tablename__ = "queues"
    __table_args__ = {'schema': 'asterisk'}
    
    name = Column(String(128), primary_key=True)
    musiconhold = Column(String(128))
    announce = Column(String(128))
    context = Column(String(128))
    timeout = Column(Integer)
    ringinuse = Column(String(10))
    setinterfacevar = Column(String(10))
    setqueuevar = Column(String(10))
    setqueueentryvar = Column(String(10))
    monitor_format = Column(String(8))
    membermacro = Column(String(512))
    membergosub = Column(String(512))
    queue_youarenext = Column(String(128))
    queue_thereare = Column(String(128))
    queue_callswaiting = Column(String(128))
    queue_quantity1 = Column(String(128))
    queue_quantity2 = Column(String(128))
    queue_holdtime = Column(String(128))
    queue_minutes = Column(String(128))
    queue_minute = Column(String(128))
    queue_seconds = Column(String(128))
    queue_thankyou = Column(String(128))
    queue_callerannounce = Column(String(128))
    queue_reporthold = Column(String(128))
    announce_frequency = Column(Integer)
    announce_to_first_user = Column(String(10))
    min_announce_frequency = Column(Integer)
    announce_round_seconds = Column(Integer)
    announce_holdtime = Column(String(128))
    announce_position = Column(String(10))
    announce_position_limit = Column(Integer)
    periodic_announce = Column(String(50))
    periodic_announce_frequency = Column(Integer)
    relative_periodic_announce = Column(String(10))
    random_periodic_announce = Column(String(10))
    retry = Column(Integer)
    wrapuptime = Column(Integer)
    penaltymemberslimit = Column(Integer)
    autofill = Column(String(10))
    monitor_type = Column(String(128))
    autopause = Column(String(10))
    autopausedelay = Column(Integer)
    autopausebusy = Column(String(10))
    autopauseunavail = Column(String(10))
    maxlen = Column(Integer)
    servicelevel = Column(Integer)
    strategy = Column(String(128))
    joinempty = Column(String(128))
    leavewhenempty = Column(String(128))
    reportholdtime = Column(String(10))
    memberdelay = Column(Integer)
    weight = Column(Integer)
    timeoutrestart = Column(String(10))
    defaultrule = Column(String(128))
    timeoutpriority = Column(String(128))
    
    def __repr__(self):
        return f"<Queue(name={self.name})>"

# Modelo para Queue Members (asterisk) - Agentes asignados a colas
class QueueMember(Base):
    __tablename__ = "queue_members"
    __table_args__ = {'schema': 'asterisk'}
    
    uniqueid = Column(Integer, primary_key=True, autoincrement=True)
    membername = Column(String(80))
    queue_name = Column(String(80))
    interface = Column(String(80))
    penalty = Column(Integer)
    paused = Column(Integer)
    state_interface = Column(String(80))
    
    def __repr__(self):
        return f"<QueueMember(membername={self.membername}, queue={self.queue_name})>"

# Modelo para Queue Rules (asterisk) - Reglas de colas
class QueueRule(Base):
    __tablename__ = "queue_rules"
    __table_args__ = {'schema': 'asterisk'}
    
    rule_name = Column(String(80), primary_key=True)
    time = Column(String(32), primary_key=True)
    min_penalty = Column(String(32))
    max_penalty = Column(String(32))
    
    def __repr__(self):
        return f"<QueueRule(rule_name={self.rule_name})>"
