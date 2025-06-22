from flask import Blueprint, Flask, jsonify
import subprocess
import os
import platform

app = Flask(__name__)

common_transactions_bp = Blueprint("common_transactions", __name__)

@common_transactions_bp.route('/runrdg', methods=['GET'])
def run_rdg():
    try:
        if platform.system() == "Windows":
            # Windows에서 백그라운드로 RDG.py 실행
            with open(os.devnull, 'w') as devnull:
                current_directory = os.getcwd()  # 현재 작업 디렉토리
                path = os.path.join(current_directory, 'Data', 'exeRDG.py')  # RDG.py 경로

                # subprocess로 RDG.py 실행
                process = subprocess.Popen(
                    ['python', path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,  # 텍스트 형식으로 출력
                    encoding='cp949'  # 한글 출력 처리
                )

                # 출력 및 오류 캡처
                stdout, stderr = process.communicate()

                # 출력 확인
                print("stdout:", stdout)
                print("stderr:", stderr)
                print(f"rund.py is running with PID: {process.pid}")

        else:
            # Unix (Linux, macOS)에서 nohup을 사용하여 백그라운드에서 RDG.py 실행
            subprocess.Popen(['nohup', 'python', 'RDG.py', '&'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return jsonify({
            'message': 'RDG.py script is running in the background.',
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'An error occurred while running the script: {str(e)}',
        }), 500
