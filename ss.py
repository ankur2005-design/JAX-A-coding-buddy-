import pyautogui
import time
import pyperclip

def ss():
    pyautogui.click(x=960 , y=540)
    time.sleep(0.1)

    pyautogui.hotkey("ctrl" , "a")
    pyautogui.hotkey("ctrl" , "c")
    time.sleep(1)
    
    code = pyperclip.paste()
    
    numbered_code = "\n".join(
        f"{i} | {line}"
        for i, line in enumerate(code.splitlines(), 1)
    )
    
    screenshot = pyautogui.screenshot()

    return screenshot , numbered_code