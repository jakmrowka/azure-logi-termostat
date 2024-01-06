import string
import datetime
from bisect import bisect_left

def diff_index(char1, char2):
    vector_index = string.ascii_uppercase + string.ascii_lowercase + string.digits
    index1 = vector_index.index(char1)
    index2 = vector_index.index(char2)

    # Obliczanie odległości
    length = abs(index1 - index2)
    return length


def convert_time(current_time, new_hour, new_minute):
    return current_time.replace(hour=new_hour, minute=new_minute, second=0)


def decode_4char(text, date):
    chars = [*text]
    minutes = 4*diff_index('A', chars[0])+round(diff_index('A', chars[1])/16)
    hours = (diff_index('A', chars[1]) % 16) * 16 + round(diff_index('A', chars[2])/4)
    temperature = diff_index('A', chars[3]) * 0.5
    return convert_time(date, hours, minutes), temperature

def get_day(text):
    if len(text) != 72:
        raise ValueError("Length must be equal 72.")
    day_length = 24
    days = {
        'weekday': text[0:day_length],
        'saturday': text[day_length:2 * day_length],
        'sunday': text[2 * day_length:3 * day_length]
    }
    return days


def set_temperature(current_time, text):
    days = get_day(text)

    day_of_week = current_time.strftime("%A").lower()
    selected_day = days['weekday'] if day_of_week not in ['saturday', 'sunday'] else days[day_of_week]
    day_before = current_time -  datetime.timedelta(days=1)
    selected_day_before = days['weekday'] if day_of_week not in ['saturday', 'sunday'] else days[day_of_week]
    schedule = selected_day_before + selected_day
    segment = 4
    day_spec = [schedule[i:i + segment] for i in range(0, len(schedule), segment)]
    hours = []
    temps = []
    for point in day_spec:
        a,b = decode_4char(point, current_time)
        hours.append(a)
        temps.append(b)
    index_position = bisect_left(hours, current_time) - 1
    # print(hours[index_position], temps[index_position])
    return temps[index_position]
