from terminal.screen import Screen
from terminal.primitives.screen_object import ScreenObject
from time import sleep

try:
    screen = Screen(20, 20, 20, 10)

    test_object = ScreenObject([
        "/-\\",
        "|#|",
        "\\-/"
    ], screen)
    cords = ScreenObject([], screen, 0, 9)

    while True:
        for i in range(-3, 11):
            x, y = i*2, i
            test_object.move(x, y)
            cords.update_content([f"x {x} y {y}"])
            screen.clear()
            test_object.draw()
            cords.draw()
            screen.update()
            sleep(1)


except Exception as e:
    print(e)

finally:
    input("")
