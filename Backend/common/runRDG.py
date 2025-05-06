from flask import Flask, jsonify
import subprocess


def run_rdg():
    try:
        # nohup을 사용하여 백그라운드에서 RDG.py를 실행
        subprocess.Popen(['nohup', 'python', 'RDG.py', '&'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return jsonify({
            'message': 'RDG.py script is running in the background.',
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'An error occurred while running the script: {str(e)}',
        }), 500