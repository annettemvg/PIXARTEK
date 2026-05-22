import sys
sys.path.insert(0, '/home/pi/pixartek/nodes/projection')
import display
display.init()
display.load_preset('flores-blancas')
display.show('/tmp/pixartek_proj_flores-blancas_2.png')
print('Projected Stage 2')
