import logging
from RPLCD.i2c import CharLCD
from threading import Event


class LCD_controller:

    '''
    Used to control and print data on lcd display
    '''

    def __init__(self) -> None:
        
        self.__lcd = CharLCD(
            i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
        )
        self.__lcd.backlight_enabled = True
        self.__lcd.display_enabled = True
        self.screen_saver_enabled = False
        self.__lcd.clear()
        
        self.__print_event = Event()
        self.__print_event.set()
        
        self.__wiring_exception_message = 'Unable to interact with lcd display, check if lcd is wired properly'

    def ready(self) -> None:
        self.__print_event.set()

    def wait(self) -> None:
        self.__print_event.wait()
        self.__print_event.clear()

    def update_lcd(self, content: list) -> None:
        
        if len(content) > 4:
            raise ValueError('Given list is too long (max lenght is 4)')
        
        if not self.screen_saver_enabled:
            self.wait()
            try:
                self.__lcd.home()
                for item in content:
                    
                    if len(item) > 20:
                        raise ValueError
                    
                    logging.info('Updating lcd')
                    self.__lcd.write_string(item + (20 - len(item)) * " ")
                    self.__lcd.crlf()
                
                for _ in range(4 - len(content)):
                    self.__lcd.write_string(20 * " ")
                    self.__lcd.crlf()
            except ValueError:
                logging.error("One of the given items is too long, max lenght is 20")
                
            except Exception:
                logging.error(self.__wiring_exception_message)
                
            self.ready()

    def disable_screen_saver(self) -> None:
        try:
            self.__lcd.display_enabled = True
            self.__lcd.backlight_enabled = True
            self.screen_saver_enabled = False
            logging.info('Screen saver is disabled')
        except Exception:
            logging.error(self.__wiring_exception_message)

    def enable_screen_saver(self) -> None:
        try:
            self.screen_saver_enabled = True
            self.__lcd.backlight_enabled = False
            self.__lcd.display_enabled = False
            logging.info('Screen saver is enabled')
        except Exception:
            logging.error(self.__wiring_exception_message)
