left = ev3_motorA()
right = ev3_motorD()

ultrasonic = ev3_ultrasonicSensor()
color = ev3_colorSensor()

# SETTINGS
DETECT_DISTANCE = 40
TAG_DISTANCE = 14

START_SPEED = 1000
SEARCH_SPEED = 300
CHARGE_SPEED = 800
PUSH_SPEED = 750

BACK_SPEED = 500
TURN_SPEED = 550

# Milliseconds
COMMAND_TIME = 180
STEP = 65

# Seconds
START_TIME = 4.0
SEARCH_TIME = 0.35
SCAN_TIME = 0.20
CHARGE_TIME = 0.5

BACK_MIN_TIME = 0.3
BACK_MAX_TIME = 0.7
TURN_TIME = 0.7
TAG_LOST_TIME = 0.3

# NEW
EDGE_COOLDOWN = 1.0
SCAN_CHANGE_TIME = 3.0


# =====================================
# MOVEMENT
# =====================================

def drive(l, r):
    ev3_runForTime(left, COMMAND_TIME, l)
    ev3_runForTime(right, COMMAND_TIME, r)
    ev3_pause(STEP)


# =====================================
# INITIAL VARIABLES
# =====================================

start = time_time()

state = "start"
until = start + START_TIME

escape_started = start
last_tag_seen = start

direction = 1
safe_count = 0

edge_armed = False
inner_count = 0

# NEW
last_edge = start - 10
next_scan_change = start + SCAN_CHANGE_TIME
tag_count = 0

print("ROBOT STARTED")


# =====================================
# MAIN LOOP
# =====================================

while True:

    now = time_time()

    c = ev3_colorSensorGetColor(color)
    distance = ev3_ultrasonicSensorDistance(ultrasonic)

    # =================================
    # ARM EDGE DETECTION
    # =====================================

    if c == 1 or c == 2 or c == 3:
        inner_count = inner_count + 1

        if inner_count >= 2:
            edge_armed = True
    else:
        inner_count = 0

    # =================================
    # EDGE DETECTION
    # =====================================

    edge = c == 4 or c == 6

    if edge and edge_armed and state != "escape":

        print("EDGE! REVERSING")

        state = "escape"
        escape_started = now
        safe_count = 0

        last_edge = now   # NEW
        tag_count = 0    # NEW

    # =================================
    # START: CHARGE TO CENTRE
    # =====================================

    if state == "start":

        l = START_SPEED
        r = START_SPEED

        if now >= until:

            if not edge_armed:
                state = "escape"
                escape_started = now
                safe_count = 0
                last_edge = now

            else:
                state = "search"
                until = now + SEARCH_TIME

    # =================================
    # ESCAPE FROM EDGE
    # =====================================

    elif state == "escape":

        l = -BACK_SPEED
        r = -BACK_SPEED

        if c == 1 or c == 2 or c == 3:
            safe_count = safe_count + 1
        else:
            safe_count = 0

        if (
            safe_count >= 2 and
            now - escape_started >= BACK_MIN_TIME
        ):
            state = "turn"
            until = now + TURN_TIME

        elif now - escape_started >= BACK_MAX_TIME:
            state = "turn"
            until = now + TURN_TIME

    # =================================
    # TURN AWAY FROM EDGE
    # =====================================

    elif state == "turn":

        l = direction * TURN_SPEED
        r = -direction * TURN_SPEED

        if now >= until:

            direction = -direction
            state = "search"
            until = now + SEARCH_TIME

    # =================================
    # SEARCH
    # =====================================

    elif state == "search":

        if (
            distance > 0 and
            distance < DETECT_DISTANCE and
            now - last_edge > EDGE_COOLDOWN
        ):

            print("CHARGE!")

            state = "charge"
            until = now + CHARGE_TIME

            tag_count = 0

            l = CHARGE_SPEED
            r = CHARGE_SPEED

        elif now >= until:

            state = "scan"
            until = now + SCAN_TIME

            l = direction * TURN_SPEED
            r = -direction * TURN_SPEED

        else:

            l = SEARCH_SPEED
            r = SEARCH_SPEED

    # =================================
    # SCAN
    # =====================================

    elif state == "scan":

        # NEW: Change scanning direction
        # after a few seconds.

        if now >= next_scan_change:

            direction = -direction
            next_scan_change = now + SCAN_CHANGE_TIME

        if (
            distance > 0 and
            distance < DETECT_DISTANCE and
            now - last_edge > EDGE_COOLDOWN
        ):

            print("CHARGE!")

            state = "charge"
            until = now + CHARGE_TIME

            tag_count = 0

            l = CHARGE_SPEED
            r = CHARGE_SPEED

        elif now >= until:

            state = "search"
            until = now + SEARCH_TIME

            l = SEARCH_SPEED
            r = SEARCH_SPEED

        else:

            l = direction * TURN_SPEED
            r = -direction * TURN_SPEED

    # =================================
    # CHARGE WITH FIXED SHOVEL
    # =====================================

    elif state == "charge":

        l = CHARGE_SPEED
        r = CHARGE_SPEED

        # NEW: Confirm opponent is close
        # for two consecutive readings.

        if distance > 0 and distance < TAG_DISTANCE:
            tag_count = tag_count + 1
        else:
            tag_count = 0

        if tag_count >= 2:

            print("TAGGED!")

            state = "push"
            last_tag_seen = now

            l = PUSH_SPEED
            r = PUSH_SPEED

        elif now >= until:

            state = "scan"
            until = now + SCAN_TIME

            l = direction * TURN_SPEED
            r = -direction * TURN_SPEED

    # =================================
    # TAGGED: KEEP PUSHING
    # =====================================

    elif state == "push":

        l = PUSH_SPEED
        r = PUSH_SPEED

        if distance > 0 and distance < 22:
            last_tag_seen = now

        if now - last_tag_seen > TAG_LOST_TIME:

            print("TARGET LOST")

            state = "scan"
            until = now + SCAN_TIME

            l = direction * TURN_SPEED
            r = -direction * TURN_SPEED

    # =================================
    # EXECUTE MOVEMENT
    # =====================================

    drive(l, r)
