class TestRule(Rule):
    def __init__(self):
        self.logger = oh.getLogger("Gesture sensor")
        self.logger.info("Regla Gesture sensor refrescada")
        self.index = 0
        self.colors = [0,60,120,180,240]
        self.gr_hue_interruptores = ir.getItem("gr_hue_interruptores")
        self.gr_hue_colores = ir.getItem("gr_hue_colores")
        self.escena = ir.getItem("hue_interruptor_escena")

    def getEventTrigger(self):
        return [
            UpdatedEventTrigger("gesture_sensor_event")
        ]

    def execute(self, event):
        command = str(event.newState)
        if (command == "right"):
            if (self.index >= len(self.colors)-1): self.index = 0
            else: self.index += 1
            new_color = str(self.colors[self.index]) + ",100,100"            
            oh.sendCommand(self.gr_hue_colores, new_color)
        if (command == "left"):
            oh.sendCommand(self.gr_hue_colores, "0,0,100")
        if (command == "up"):
            oh.sendCommand(self.gr_hue_interruptores, "ON")
        if (command == "down"):
            oh.sendCommand(self.gr_hue_interruptores, "OFF")
        if (command == "near"):
            oh.sendCommand(self.escena, "OFF")
        if (command == "far"):
            oh.sendCommand(self.escena, "ON")

def getRules():
    return RuleSet([
        TestRule()
    ])
