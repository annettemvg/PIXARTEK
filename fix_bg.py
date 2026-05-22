for f, old, new in [
    ('/home/pi/pixartek/nodes/projection/display.py', '(0, 0, 0)', '(255, 255, 255)'),
    ('/home/pi/pixartek/nodes/projection/display_daemon.py', 'screen.fill((0, 0, 0))', 'screen.fill((255, 255, 255))'),
]:
    t = open(f, 'rb').read().decode('utf-8-sig')
    t = t.replace(old, new)
    open(f, 'w').write(t)
    print(f'Fixed: {f}')
print('All done')
