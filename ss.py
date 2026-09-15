import pyautogui
import time
import pyperclip

def ss():
    screenshot = pyautogui.screenshot()
    time.sleep(1)
    
    pyautogui.click(x=960 , y=540)
    time.sleep(1)

    pyautogui.hotkey("ctrl" , "a")
    pyautogui.hotkey("ctrl" , "c")
    code = pyperclip.paste()

    return screenshot , code