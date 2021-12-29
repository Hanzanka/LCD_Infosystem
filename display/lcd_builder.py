from RPLCD.i2c import CharLCD

class LCD:
    
    '''
    Used to construct the CharLCD-object. Also used to provide CharLCD-object to other classes
    '''
    
    def __init__(self) -> None:
        self.lcd = CharLCD(
            i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
        )
        self.lcd.backlight_enabled = False
        self.lcd.display_enabled = True
        self.lcd.clear()

    def get_lcd(self) -> CharLCD:
        return self.lcd

if __name__ == "__main__":
    lcd = LCD()
    lcd.lcd.display_enabled = False
