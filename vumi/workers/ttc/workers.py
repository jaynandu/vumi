# -*- test-case-name: vumi.workers.ttc.tests.test_ttc -*-

from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from twisted.enterprise import adbapi

from twistar.dbobject import DBObject
from twistar.registry import Registry

from vumi.application import ApplicationWorker
from vumi.message import Message
from vumi.application import SessionManager

#from vumi.database.base import setup_db, get_db, close_db, UglyModel

#class ParticipantModel(UglyModel):
    #TABLE_NAME = 'participant_items'
    #fields = (
        #('id', 'SERIAL PRIMARY KEY'),
        #('phone_number','int8 UNIQUE NOT NULL'),
        #)
    #indexes = ('phone_number',)
    
    #@classmethod
    #def get_items(cls, txn):
        #items = cls.run_select(txn,'')
        #if items:
            #items[:] = [cls(txn,*item) for item in items]
            #return items
            ##return cls(txn, *items[0])
        #return None
    
    #@classmethod
    #def create_item(cls, txn, number):
        #params = {'phone_number': number}
        #txn.execute(cls.insert_values_query(**params),params)
        #txn.execute("SELECT lastval()")
        #return txn.fetchone()[0]

#Models#
#CREATE TABLE dialogues (id SERIAL PRIMARY KEY, name VARCHAR(50),type VARCHAR(20)) 
#CREATE TABLE interactions (id SERIAL PRIMARY KEY, name VARCHAR, content VARCHAR(50), schedule_type VARCHAR(30), dialogue_id INT)
#CREATE TABLE schedules (id SERIAL PRIMARY KEY, type VARCHAR(30), interaction_id INT)

#Model Relations#
class Dialogue(DBObject):
    HASMANY=['interactions']
    
class Interaction(DBObject):
    BELONGSTO=['dialogue']

#class Schedule(DBObject):
    #BELONGSTO=['interaction']

Registry.register(Dialogue, Interaction)

class TtcGenericWorker(ApplicationWorker):
    
    @inlineCallbacks
    def startWorker(self):
        super(TtcGenericWorker, self).startWorker()
        self.control_consumer = yield self.consume(
            '%(transport_name)s.control' % self.config,
            self.consume_control,
            message_class=Message)

        #some basic local recording
        self.record = []

        # Try to access database with Ugly model
        #self.setup_db = setup_db(ParticipantModel)
        #self.db = setup_db('test', database='test',
        #         user='vumi',
        #         password='vumi',
        #         host='localhost')
        #self.db.runQuery('SELECT 1')
    
        # Try to Access Redis
        #self.redis = SessionManager(db=0, prefix="test")
        
        # Try to Access database with twistar
        def done(result):
            print "Got connection to database %s" %result
        Registry.DBPOOL = adbapi.ConnectionPool('psycopg2', "dbname=test host=localhost user=vumi password=vumi")
        yield Registry.DBPOOL.runQuery("SELECT 1").addCallback(done)
    
    def consume_user_message(self, message):
        log.msg("User message: %s" % message['content'])
    
    @inlineCallbacks
    def consume_control(self, message):
        log.msg("Control message!")
        #data = message.payload['data']
        if (message.get('program')):
            log.msg("received a program")
            program = message.get('program')
            log.msg("Start the program %s" % program.get('name'))
            self.record.append(('config',message))
            
            #Redis#
            #self.redis.create_session("program")
            #self.redis.save_session("program", program)
            #session = self.redis.load_session("program")
            #log.msg("Message stored and retrieved %s" % session.get('name'))
            
            #UglyModel#
            #self.db.runInteraction(ParticipantModel.create_item,68473)        
            #name = program.get('name')
            #group = program.get('group',{})
            #number = group.get('number')
            #log.msg("Control message %s to be add %s" % (number,name))
      
            #Twistar#                
            def failure(error):
                log.msg("failure while saving %s" %error)
                
            dialogues = program.get('dialogues')
            if (dialogues):
                for dialogue in dialogues:
                    #oDialogue = yield Dialogue(name=dialogue.get('name'),type=dialogue.get('type')).save().addCallback(onDialogueSave,dialogue.get('interactions')).addErrback(failure)
                    oDialogue = yield Dialogue.find(where=['name = ?',dialogue.get('name')], limit=1)
                    if (oDialogue==None):
                        oDialogue = yield Dialogue(name=dialogue.get('name'),type=dialogue.get('type')).save().addErrback(failure)
                    else:
                        oDialogue.name = dialogue.get('name')
                        oDialogue.save()
                    for interaction in dialogue.get('interactions'):
                        if interaction.get('type')== "announcement":
                            oInteraction = yield Interaction.find(where=['name = ?',interaction.get('name')], limit=1)
                            if (oInteraction==None):
                                oInteraction = yield Interaction(content=interaction.get('content'),
                                                                 name=interaction.get('name'),
                                                                 schedule_type=interaction.get('schedule_type'), 
                                                                 dialogue_id=oDialogue.id).save().addErrback(failure)
                            else:
                                oInteraction.content = interaction.get('content')
                                oInteraction.name = interaction.get('name')
                                oInteraction.schedule_type=interaction.get('schedule_type')
                                oInteraction.save()
                            #yield Schedule(type=interaction.get("schedule_type"),
                                           #interaction_id=oInteraction.id).save()
        
        elif (message.get('phones')):
            log.msg("received a list of phone")
            phones = message.get("phone")
            self.record.append(('config',message))
            


        #for dialogue in dialogues:
            #yield Message(name=dialogue.get('name')).save()
    
    def dispatch_event(self, message):
        log.msg("Event message!")
    