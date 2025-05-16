from datetime import datetime, time, timedelta

class TimeCalculator:
    WORKDAY_START = time(7, 45)
    WORKDAY_END = time(17, 45)  # Horario de L-J
    FRIDAY_END = time(16, 45)   # Horario especial de viernes
    BREAK_START = time(13, 0)
    BREAK_END = time(14, 0)
    WORK_HOURS = 9  # L-J
    FRIDAY_HOURS = 8  # Viernes

    @staticmethod
    def is_working_day(date):
        """Determina si una fecha es día laboral (L-V)"""
        return date.weekday() < 5
    
    @staticmethod
    def get_next_working_day(date):
        """Obtiene el siguiente día laboral"""
        next_day = date + timedelta(days=1)
        while not TimeCalculator.is_working_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def get_workday_end(self, date):
        """Obtiene la hora de fin según el día de la semana"""
        return self.FRIDAY_END if date.weekday() == 4 else self.WORKDAY_END

    def get_work_hours(self, date):
        """Obtiene las horas laborables según el día de la semana"""
        return self.FRIDAY_HOURS if date.weekday() == 4 else self.WORK_HOURS

    def calculate_working_days(self, start_date, cantidad, estandar):
        """
        Implementación del cálculo de días laborables considerando horario especial de viernes
        """
        if not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, self.WORKDAY_START)

        if not estandar or estandar <= 0:
            return {
                'intervals': [],
                'start_date': start_date.date() if isinstance(start_date, datetime) else start_date,
                'end_date': start_date.date() if isinstance(start_date, datetime) else start_date,
                'next_available_time': start_date,
                'error': 'El estándar debe ser mayor que 0'
            }

        current_date = start_date.date()
        current_datetime = start_date
        remaining_units = float(cantidad)
        intervals = []

        # El estándar ya viene por hora
        estandar_hora = float(estandar)

        # Si la fecha inicial no es día laboral, mover al siguiente día laboral
        if not self.is_working_day(current_date):
            next_day = self.get_next_working_day(current_date)
            current_datetime = datetime.combine(next_day, self.WORKDAY_START)
            current_date = current_datetime.date()

        while remaining_units > 0:
            # Si no es día laboral, pasar al siguiente
            if not self.is_working_day(current_date):
                next_day = self.get_next_working_day(current_date)
                current_datetime = datetime.combine(next_day, self.WORKDAY_START)
                current_date = current_datetime.date()
                continue

            # Obtener hora de fin según el día
            workday_end = self.get_workday_end(current_date)

            # Ajustar current_datetime si está fuera del horario laboral
            if current_datetime.time() < self.WORKDAY_START:
                current_datetime = datetime.combine(current_date, self.WORKDAY_START)
            elif current_datetime.time() > workday_end:
                next_day = self.get_next_working_day(current_date + timedelta(days=1))
                current_datetime = datetime.combine(next_day, self.WORKDAY_START)
                current_date = current_datetime.date()
                continue

            # Procesar por horas
            hora_actual = current_datetime
            while hora_actual.time() < workday_end and remaining_units > 0:
                # Si estamos en la hora de descanso, saltar a la siguiente hora
                if self.BREAK_START <= hora_actual.time() < self.BREAK_END:
                    hora_actual = datetime.combine(current_date, self.BREAK_END)
                    continue

                # Calcular el fin del intervalo actual (próxima hora o límite)
                next_hour = (hora_actual + timedelta(hours=1)).replace(minute=0, second=0)
                if next_hour.time() > workday_end:
                    next_hour = datetime.combine(current_date, workday_end)
                if hora_actual.time() < self.BREAK_START and next_hour.time() > self.BREAK_START:
                    next_hour = datetime.combine(current_date, self.BREAK_START)

                # Calcular unidades para esta hora
                hours_in_interval = (next_hour - hora_actual).total_seconds() / 3600
                units_this_interval = min(remaining_units, hours_in_interval * estandar_hora)

                if units_this_interval > 0:
                    interval = {
                        'fecha': current_date,
                        'fecha_inicio': hora_actual,
                        'fecha_fin': next_hour,
                        'unidades': units_this_interval,
                        'unidades_restantes': remaining_units - units_this_interval,
                        'continue_same_day': next_hour.time() < workday_end and next_hour.time() != self.BREAK_START
                    }
                    intervals.append(interval)
                    remaining_units -= units_this_interval

                hora_actual = next_hour

            # Si quedan unidades, preparar para el siguiente día
            if remaining_units > 0:
                last_interval = intervals[-1] if intervals else None
                if last_interval and last_interval['continue_same_day']:
                    current_datetime = last_interval['fecha_fin']
                else:
                    next_day = self.get_next_working_day(current_date)
                    current_datetime = datetime.combine(next_day, self.WORKDAY_START)
                    current_date = current_datetime.date()

        return {
            'intervals': intervals,
            'start_date': intervals[0]['fecha'] if intervals else current_date,
            'end_date': intervals[-1]['fecha'] if intervals else current_date,
            'next_available_time': intervals[-1]['fecha_fin'] if intervals else current_datetime
        }
    
    def calculate_process_duration(self, cantidad, estandar):
        """
        Calcula la duración total de un proceso
        """
        if not estandar or estandar <= 0:
            return timedelta(0)
        
        calculo = self.calculate_working_days(
            datetime.now().replace(hour=self.WORKDAY_START.hour, minute=self.WORKDAY_START.minute),
            cantidad,
            estandar
        )
        
        if 'error' in calculo:
            return timedelta(0)
        
        return calculo['next_available_time'] - calculo['intervals'][0]['fecha_inicio']