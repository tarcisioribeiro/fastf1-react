"""
Utility functions for API endpoints.
"""


def explain_crontab(crontab_str):
    """
    Converte uma expressão crontab em uma descrição legível em português.

    Formato crontab: minute hour day_of_month month_of_year day_of_week
    Exemplo: "0 */6 * * *" -> "A cada 6 horas"

    Args:
        crontab_str: String no formato "minute hour day_of_month month_of_year day_of_week"

    Returns:
        String com descrição em português
    """
    try:
        parts = crontab_str.strip().split()
        if len(parts) != 5:
            return "Formato de crontab inválido"

        minute, hour, day_of_month, month_of_year, day_of_week = parts

        # Casos especiais comuns
        if crontab_str == "* * * * *":
            return "A cada minuto"

        if minute.startswith("*/") and hour == "*" and day_of_month == "*" and month_of_year == "*" and day_of_week == "*":
            interval = minute[2:]
            return f"A cada {interval} minuto(s)"

        if minute == "0" and hour.startswith("*/") and day_of_month == "*" and month_of_year == "*" and day_of_week == "*":
            interval = hour[2:]
            return f"A cada {interval} hora(s)"

        if minute == "0" and hour == "*" and day_of_month == "*" and month_of_year == "*" and day_of_week == "*":
            return "A cada hora"

        if minute == "0" and hour == "0" and day_of_month == "*" and month_of_year == "*" and day_of_week == "*":
            return "Todo dia à meia-noite"

        if minute == "0" and hour == "12" and day_of_month == "*" and month_of_year == "*" and day_of_week == "*":
            return "Todo dia ao meio-dia"

        if minute == "0" and hour == "0" and day_of_month == "1" and month_of_year == "*" and day_of_week == "*":
            return "Todo dia 1º de cada mês à meia-noite"

        if minute == "0" and hour == "0" and day_of_month == "*" and month_of_year == "*" and day_of_week == "0":
            return "Todo domingo à meia-noite"

        if minute == "0" and hour == "0" and day_of_month == "*" and month_of_year == "*" and day_of_week == "1":
            return "Toda segunda-feira à meia-noite"

        # Construir descrição customizada
        parts_desc = []

        # Minuto
        if minute == "*":
            pass  # Não mencionar se for todo minuto
        elif minute.startswith("*/"):
            parts_desc.append(f"a cada {minute[2:]} minuto(s)")
        elif minute.isdigit():
            parts_desc.append(f"no minuto {minute}")
        else:
            parts_desc.append(f"nos minutos {minute}")

        # Hora
        if hour == "*":
            if not parts_desc:
                parts_desc.append("a cada hora")
        elif hour.startswith("*/"):
            parts_desc.append(f"a cada {hour[2:]} hora(s)")
        elif hour.isdigit():
            parts_desc.append(f"às {hour}h")
        else:
            parts_desc.append(f"nas horas {hour}")

        # Dia do mês
        if day_of_month != "*":
            if day_of_month.startswith("*/"):
                parts_desc.append(f"a cada {day_of_month[2:]} dia(s)")
            elif day_of_month.isdigit():
                parts_desc.append(f"no dia {day_of_month}")
            else:
                parts_desc.append(f"nos dias {day_of_month}")

        # Mês
        if month_of_year != "*":
            months = {
                "1": "janeiro", "2": "fevereiro", "3": "março", "4": "abril",
                "5": "maio", "6": "junho", "7": "julho", "8": "agosto",
                "9": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro"
            }
            if month_of_year.isdigit():
                month_name = months.get(month_of_year, month_of_year)
                parts_desc.append(f"em {month_name}")
            else:
                parts_desc.append(f"nos meses {month_of_year}")

        # Dia da semana
        if day_of_week != "*":
            days = {
                "0": "domingo", "1": "segunda-feira", "2": "terça-feira",
                "3": "quarta-feira", "4": "quinta-feira", "5": "sexta-feira",
                "6": "sábado", "7": "domingo"
            }
            if day_of_week.isdigit():
                day_name = days.get(day_of_week, day_of_week)
                parts_desc.append(f"às {day_name}s")
            else:
                parts_desc.append(f"nos dias {day_of_week}")

        if not parts_desc:
            return "Sempre"

        # Capitalizar primeira letra
        description = ", ".join(parts_desc)
        return description[0].upper() + description[1:]

    except Exception as e:
        return f"Erro ao interpretar crontab: {str(e)}"
