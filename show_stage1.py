import sys
sys.path.insert(0, '/home/pi/pixartek/nodes/projection')
import display
display.init()
display.load_preset('flores-blancas-1')
display.show('/tmp/pixartek_proj_flores-blancas_1.png')
print('Projected Etapa 1 at saved position')
