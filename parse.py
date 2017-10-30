from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from db import SQLightHelper
import config

MPEI_SCHEDULE_URL = 'http://mpei.ru/Education/timetable/Pages/default.aspx'


class MPEIParser:
    def __init__(self, path):
        self.path = path
        self.table = None
        self.group_id = None

    def _get_schedule(self, group):
        driver = webdriver.PhantomJS(self.path)
        try:
            driver.maximize_window()

            driver.get(MPEI_SCHEDULE_URL)
            search_field = driver.find_element_by_id('myGroup')
            search_field.send_keys(group)
            search_field.send_keys(Keys.ENTER)
            if len(driver.window_handles) != 1:
                driver.switch_to.window(driver.window_handles[1])
                href_block = driver.find_element_by_class_name('mpei-tt-linkedlist')
                href = href_block.find_element_by_partial_link_text('Расписание')
                href.click()
                try:
                    table = driver.find_element_by_class_name('mpei-tt-grid-wrap')
                    self.table = parse_table(table.get_attribute('innerHTML'))
                    return True
                except NoSuchElementException:
                    return False
                    # print(table)
            else:
                return False
                # driver.save_screenshot('foo.png')
        finally:
            driver.quit()

    def get_by_day(self, SQLightHelper, group, day, week=1, string=True):
        db = SQLightHelper
        group_id = db.select_group_id(group)
        self.group_id = group_id
        if db.select_lessons_by_day(group_id, week, day):  # if there is schedule in db, load from db
            lessons = []
            lessons.append(db.select_lessons_by_day(group_id, week, day))
            if string:
                # print(lessons)
                if week == 1:
                    return str("Нечетная неделя:\n" + lessons[0][0] + '\n' + lessons[0][1] + '\n' +
                               lessons[0][2] + '\n' + lessons[0][3] + "\n" + lessons[0][4])
                else:
                    return str("Четная неделя:\n" + lessons[0][0] + '\n' + lessons[0][1] + '\n' +
                               lessons[0][2] + '\n' + lessons[0][3] + "\n" + lessons[0][4])
            else:
                return lessons

        status = True
        if self.table is None:  # parse schedule
            status = self._get_schedule(group)

        if status:  # if parsing was successful return schedule
            table = self.table
            if string:
                if week == 1:
                    self._save_lessons_db(db)
                    return str("Нечетная неделя:\n" + table[0][(day - 1) * 2] + '\n' + table[1][(day - 1) * 2] + '\n' +
                               table[2][(day - 1) * 2] + '\n' + table[3][(day - 1) * 2] + '\n' + table[4][(day - 1) * 2])
                else:
                    self._save_lessons_db(db)
                    return str("Четная неделя:\n" + table[0][day * 2 - 1] + '\n' + table[1][day * 2 - 1] + '\n' +
                               table[2][day * 2 - 1] + '\n' + table[3][day * 2 - 1] + "\n" + table[4][day * 2 - 1])
            else:
                lessons = []
                if week == 1:
                    for i in range(0, 5):
                        lessons.append(table[i][day * 2 - 1])
                else:
                    for i in range(0, 5):
                        lessons.append(table[i][(day - 1) * 2])
                self._save_lessons_db(db)
                return lessons
        else:
            return False

    def _save_lessons_db(self, db):
        for day in range(1, 7):
            for number in range(1, 6):
                db.save_lesson(day=day, week=1, lesson=self.table[number - 1][(day - 1) * 2], group_id=self.group_id,
                               number=number)
                db.save_lesson(day=day, week=2, lesson=self.table[number - 1][day * 2 - 1], group_id=self.group_id,
                               number=number)


def parse_table(element):
    soup = BeautifulSoup(element, "html.parser")
    table = soup.find("table")
    headings = [th.get_text() for th in table.find("tr").find_all("th")]
    headings.pop(0)
    # print(headings)

    original_table = []
    all_day = {}
    for row in table.find_all("tr")[2:]:
        cells = row.find_all('td')[1:]
        new_row = []
        i = 0
        for cell in cells:
            cell_text = cell.find(text=True)
            if cell_text is None:
                cell_text = '-----'
            new_row.append(cell_text)
            i += 1

            if check_colspan2(cell):
                new_row.append(cell_text)
                i += 1

            if check_rowspan5(cell):
                all_day[len(new_row) - 2] = cell_text

            if i in all_day:
                new_row.append(all_day[i])
                new_row.append(all_day[i])
                i += 2

        original_table.append(new_row)
    return original_table


def check_colspan2(cell):
    try:
        col = int(cell["colspan"])
        if col == 2:
            return True
        else:
            return False
    except (ValueError, KeyError) as e:
        return False


def check_rowspan5(cell):
    try:
        col = int(cell["rowspan"])
        if col == 5:
            return True
        else:
            return False
    except (ValueError, KeyError) as e:
        return False
