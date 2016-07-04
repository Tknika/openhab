## Estado 0: OFF  -> Sin reserva activa y aula apagada
## Estado 1: PRE  -> Con reserva activa, pero a la espera de movimiento para encenderse
## Estado 2: ON   -> Con reserva activa y encendida
## Estado 3: POST -> Sin reserva activa, a la espera de apagarla

import openhab
import openhab.config

timers_reservas = {}

@openhab.rule
class StepToPREandPOST(Rule):
    def __init__(self, aula):
        self.aula = aula.lower()
        self.logger = oh.getLogger("Reserva de %s" % self.aula)
        self.audio = "%s.id" % (self.aula) in openhab.config.get_config("squeeze")
        self.squeezeboxSpeak = oh.getAction("Squeezebox").squeezeboxSpeak

    def getEventTrigger(self):
        return [
            UpdatedEventTrigger("%s_reserva_activa" % (self.aula))
        ]

    def aula_off(self):
        oh.sendCommand(self.interruptores, "OFF")
        oh.sendCommand(self.reserva_estado_item, "0")
        self.logger.info("Apagamos el aula por falta de movimiento, estado OFF")
        timers_reservas[self.aula].cancel()
        timers_reservas[self.aula] = None

    def execute(self, event):
        self.interruptores = ir.getItem("gr_%s_interruptores" % (self.aula))
        self.reserva_estado_item = ir.getItem("%s_reserva_estado" % (self.aula))        
        reserva_activa = str(ir.getItem("%s_reserva_activa" % (self.aula)).state)
        reserva_estado = int(str(ir.getItem("%s_reserva_estado" % (self.aula)).state))
        if reserva_activa == "ON":
            if reserva_estado == 0 or reserva_estado == 3:
                if not timers_reservas[self.aula] is None:
                    timers_reservas[self.aula].cancel()
                    timers_reservas[self.aula] = None
                self.logger.info("Reserva activa, pasamos al estado PRE")
                oh.sendCommand(self.reserva_estado_item, 1)
        elif reserva_activa == "OFF" and reserva_estado != 0:
            oh.sendCommand(self.reserva_estado_item, 3)
            self.logger.info("Reserva no activa, pasamos al estado POST y creamos el timer")
            timers_reservas[self.aula] = oh.createTimer(DateTime.now().plusMinutes(2), self.aula_off)
            if self.audio: self.squeezeboxSpeak(self.aula, u"Fin de la reserva, el aula se apagará en breve", 100, False)


@openhab.rule
class StepFromPREToON(Rule):
    def __init__(self, aula):
        self.aula = aula.lower()
        self.logger = oh.getLogger("Reserva de %s" % self.aula)
        self.audio = "%s.id" % (self.aula) in openhab.config.get_config("squeeze")
        self.squeezeboxSpeak = oh.getAction("Squeezebox").squeezeboxSpeak

    def getEventTrigger(self):
        return [
            ChangedEventTrigger("gr_%s_presencia" % (self.aula)),
            ChangedEventTrigger("gr_%s_puertas" % (self.aula))
        ]

    def execute(self, event):
        interruptores = ir.getItem("gr_%s_interruptores" % (self.aula))
        reserva_estado_item = ir.getItem("%s_reserva_estado" % (self.aula))        
        reserva_estado = int(str(reserva_estado_item.state))
        if reserva_estado == 1:
            self.logger.info("Encendemos el aula porque se ha detectado movimiento, estado ON")
            oh.sendCommand(interruptores, "ON")
            oh.sendCommand(reserva_estado_item, "2")
            hora = str(ir.getItem("%s_reserva_fin" % (self.aula)).state.format("%1$tl"))
            minutos = str(ir.getItem("%s_reserva_fin" % (self.aula)).state.format("%1$tM"))
            mensaje_bienvenida = "Bienvenido, su reserva finaliza a las %s y %s" % (hora, minutos)
            if self.audio: self.squeezeboxSpeak(self.aula, mensaje_bienvenida, 100, False)


@openhab.rule
class StepFromPOSTToOFF(Rule):
    def __init__(self, aula):
        self.aula = aula.lower()
        self.logger = oh.getLogger("Reserva de %s" % self.aula)
        self.audio = "%s.id" % (self.aula) in openhab.config.get_config("squeeze")
        self.squeezeboxSpeak = oh.getAction("Squeezebox").squeezeboxSpeak
    
    def aula_off(self):
        oh.sendCommand(self.interruptores, "OFF")
        oh.sendCommand(self.reserva_estado_item, "0")
        self.logger.info("Apagamos el aula por falta de movimiento, estado OFF")
        timers_reservas[self.aula].cancel()
        timers_reservas[self.aula] = None

    def getEventTrigger(self):
        return [
            ChangedEventTrigger("gr_%s_presencia" % (self.aula))
        ]

    def execute(self, event):
        self.interruptores = ir.getItem("gr_%s_interruptores" % (self.aula))
        self.reserva_estado_item = ir.getItem("%s_reserva_estado" % (self.aula))        
        reserva_estado = int(str(self.reserva_estado_item.state))
        presencia = str(ir.getItem("gr_%s_presencia" % (self.aula)).state)

        if reserva_estado == 3:
            if presencia == "OPEN":
                if not timers_reservas[self.aula] is None:
                    timers_reservas[self.aula].cancel()
                    timers_reservas[self.aula] = None
            elif presencia == "CLOSED":
                if timers_reservas[self.aula] is None:
                    timers_reservas[self.aula] = oh.createTimer(DateTime.now().plusMinutes(2), self.aula_off)
                

def getRules():
    aulas = ["nafarroa103","nafarroa_behera104","lapurdi105","zuberoa106","smc_festo107","urdaburu108"]
    for aula in aulas: timers_reservas[aula] = None
    reglas = []
    for aula in aulas: reglas.append(StepToPREandPOST(aula))
    for aula in aulas: reglas.append(StepFromPREToON(aula))
    for aula in aulas: reglas.append(StepFromPOSTToOFF(aula))
    return RuleSet(
        reglas
    )
