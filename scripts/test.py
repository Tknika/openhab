class TestRule(Rule):
    def __init__(self):
        self.logger = oh.getLogger("TestRule")

    def getEventTrigger(self):
        return [
            TimerTrigger("0 0 * * * ?")
        ] 

    def execute(self, event):
        self.logger.info("Hola")

def getRules():
    return RuleSet([
        TestRule()
    ])
