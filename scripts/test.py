import openhab
import openhab.quartz

@openhab.rule
class TestRule(Rule):
    def __init__(self):
        self.logger = oh.getLogger("TestRule")
        openhab.quartz.log_jobs()   


    def getEventTrigger(self):
        return [
            TimerTrigger("0 0 * * * ?")
        ] 

    def execute(self, event):
        #self.logger.info("Hola")
        pass

def getRules():
    return RuleSet([
        TestRule()
    ])
