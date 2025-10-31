   def demo_cb(p: Position):
        print("Nova posição:", p)

    t = GPSTracker(serial_port=args.port, baudrate=args.baud)
    t.set_callback(demo_cb)
    t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Parando...")
        t.stop()
