import datetime
import openhab
import openhab.config

@openhab.rule
class LimpiezaAulas(Rule):
    def __init__(self, aula):
        self.aula = aula.lower()
        self.logger = oh.getLogger("Limpieza en " + self.aula)
        self.mensaje_bienvenida = u"Energía habilitada durante diez minutos"
        self.mensaje_off = u"Apagamos el aula por falta de movimiento"
        self.mensaje_aviso = u"En un minuto se apagará el aula por falta de movimiento"
        self.mensaje_postpuesto = u"Apagado postpuesto hasta dentro de 10 minutos"
        self.aula_en_uso = False
        self.aula_en_aviso = False
        self.timer_warn = None
        self.timer_off = None
        self.audio = "%s.id" % (self.aula) in openhab.config.get_config("squeeze")
        self.squeezeboxSpeak = oh.getAction("Squeezebox").squeezeboxSpeak
        self.interruptores_aula = ir.getItem("gr_%s_interruptores" % (self.aula))
        self.logger.info("Regla de limpieza en %s correctamente iniciada (Audio: %s)" % (self.aula, self.audio))

    def warn_function(self):
        self.logger.info(self.mensaje_aviso)
        self.timer_warn.cancel()
        self.timer_warn = None
        self.aula_en_aviso = True
        if self.audio: self.squeezeboxSpeak(self.aula, self.mensaje_aviso, 100, False)
        
    def off_function(self):
        self.logger.info(u"Ha pasado el tiempo fijado, asi que vamos a poner los timers a null otra vez")
        estado_reserva = int(str(ir.getItem("%s_reserva_estado" % (self.aula)).state))
        self.timer_off.cancel()
        self.timer_off = None
        self.aula_en_uso = False
        self.aula_en_aviso = False
        if estado_reserva == 0:
            self.logger.info(u"Vamos a apagar las luces")
            oh.sendCommand(self.interruptores_aula, "OFF")
            if self.audio: self.squeezeboxSpeak(self.aula, self.mensaje_off, 100, False)
        

    def getEventTrigger(self):
        return [
            ChangedEventTrigger("gr_%s_presencia" % (self.aula)),
            ChangedEventTrigger("gr_%s_puertas" % (self.aula))
        ]

    def execute(self, event):
        hora = datetime.datetime.now().hour
        limpieza_hora_inicio = int(str(ir.getItem("limpieza_hora_inicio").state))
        limpieza_hora_fin = int(str(ir.getItem("limpieza_hora_fin").state))
        limpieza_tiempo_on = int(str(ir.getItem("limpieza_tiempo_on").state))
        estado_reserva = int(str(ir.getItem("%s_reserva_estado" % (self.aula)).state))

        if (hora >= limpieza_hora_inicio) and (hora < limpieza_hora_fin) and (estado_reserva == 0):
            estado_presencia = str(ir.getItem("gr_%s_presencia" % (self.aula)).state)
            puertas = ir.getItem("gr_%s_puertas" % (self.aula)) 

            if estado_presencia == "OPEN" or pe.changedSince(puertas, DateTime.now().plusMinutes(2)):
                if (self.timer_off is None and not self.aula_en_uso):
                    self.logger.info("El timer es null, asi que vamos a encender los interruptores")
                    oh.sendCommand(self.interruptores_aula, "ON")
                    self.aula_en_uso = True
                    if self.audio: self.squeezeboxSpeak(self.aula, self.mensaje_bienvenida, 100, False)
                else:
                    self.logger.info("Movimiento detectado pero el timer no es null, lo cancelamos hasta que aparezca un CLOSED")
                    self.timer_off.cancel()
                    self.timer_off = None
                    if not self.timer_warn is None:
                        self.timer_warn.cancel()
                        self.timer_warn = None            
                    if self.aula_en_aviso:
                        self.aula_en_aviso = False
                        if self.audio: self.squeezeboxSpeak(self.aula, self.mensaje_postpuesto, 100, False)

            if estado_presencia == "CLOSED":
                if not self.timer_off is None:
                    self.logger.info(u"Habia un timer creado, lo cancelamos")
                    self.timer_off.cancel()
                    self.timer_off = None 
                if not self.timer_warn is None:
                    self.timer_warn.cancel()
                    self.timer_warn = None
                self.logger.info(u"Creamos el timer por falta de movimiento")
                self.timer_warn = oh.createTimer(DateTime.now().plusMinutes(limpieza_tiempo_on-1), self.warn_function)
                self.timer_off = oh.createTimer(DateTime.now().plusMinutes(limpieza_tiempo_on), self.off_function)
            


def getRules():
    aulas = ["nafarroa103","nafarroa_behera104","lapurdi105","zuberoa106","smc_festo107","urdaburu108"]
    return RuleSet([
        LimpiezaAulas(aula) for aula in aulas
    ])
