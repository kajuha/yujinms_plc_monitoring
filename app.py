from flask import Flask, render_template, request
import json
import os
import random
import struct
import inspect

from multiprocessing import Process, Queue
import time

STATE_LOOP_HZ = 10
# STATE_LOOP_HZ = 0
QUEUE_RX_STATE_CLEAR_NUM = 10
queue_rx_state = Queue()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

web_server = Process(target=app.run, args=('0.0.0.0', 5000, False))

@app.route('/')
@app.route('/index.html')
@app.route('/pages-main.html')
def dashboard_page() -> 'html':
	return render_template('pages-main.html')

@app.errorhandler(404)
def page_not_found(e) -> 'html':
	return render_template('pages-404.html'), 404

@app.errorhandler(500)
def internal_server_error(e) -> 'html':
	return render_template('pages-500.html'), 500

@app.route('/post/buttonIncrease', methods=['POST'])
def buttonIncrease() -> 'json':
	req_form = request.form.to_dict(flat=False)
	try:
		status = {}
		status['ok'] = 'clicked'
		print(status)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False, 'message': status})

@app.route('/post/getData', methods=['POST'])
def getData() -> 'json':
	global queue_rx_state
	if not queue_rx_state.empty():
		# print(queue_rx_state.qsize())
		# tx_data = queue_rx_state.get()
		# print(tx_data)

		# 큐에 있는 데이터 중 최신 데이터만 가져옴
		rx_state = []
		for i in range(queue_rx_state.qsize()):
			rx_state = queue_rx_state.get()

		status = {}
		try:
			status['display1'] = '{0:.2f}'.format(rx_state['display1'])
			status['display2'] = '{0}'.format(rx_state['display2'])
			status['display3'] = '{0:.2f}'.format(rx_state['display3'])
			# print(status)
		except Exception as e:
			print(inspect.stack()[0][3], e)
			return json.dumps({'error': True, 'message': str(e)})

		return json.dumps({'error': False, 'message': status})
	else:
		return json.dumps({'error': False, 'message': None})

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    
@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

PLC_HOST = '192.168.0.211'
PLC_PORT = 6000

import pymcprotocol
import time

def control_tcp(dummy):
	pymc3e = pymcprotocol.Type3E()

	pymc3e.setaccessopt(commtype="ascii")
	pymc3e.connect(PLC_HOST, PLC_PORT)

	ts_state_end = ts_state_start = time.time()

	while True:
		ts_state_end = time.time()
		if ts_state_end - ts_state_start > (1.0/STATE_LOOP_HZ):
			if STATE_LOOP_HZ != 0:
				ts_state_start = ts_state_end
				# print(time.time())
				
				bitunits_values = pymc3e.batchread_bitunits(headdevice="M0", readsize=1)
				# print(bitunits_values[0])

				status = {}
				status['display1'] = -2 + random.random()
				status['display2'] = bitunits_values[0]
				status['display3'] = +2 + random.random()

				global queue_rx_state
				if queue_rx_state.qsize() > QUEUE_RX_STATE_CLEAR_NUM:
					get_num_rx_state = queue_rx_state.qsize() - QUEUE_RX_STATE_CLEAR_NUM
					# print("queue_rx_state.qsize(): ", queue_rx_state.qsize(), "get_num_rx_state: ", get_num_rx_state)
					for i in range(get_num_rx_state):
						queue_rx_state.get()
				queue_rx_state.put(status)

if __name__ == '__main__':
	tcp_client = Process(target=control_tcp, args=(0, ))
	tcp_client.start()

	# Flask의 출력을 비활성화 할 경우
	import logging
	log = logging.getLogger('werkzeug')
	log.disabled = True
	# log.disabled = False

	web_server.start()

	tcp_client.join()