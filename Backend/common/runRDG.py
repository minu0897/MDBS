from flask import Blueprint, jsonify
import subprocess, os, platform

common_transactions_bp = Blueprint("common_transactions", __name__)

@common_transactions_bp.route('/runrdg', methods=['GET'])
def run_rdg():
    current_directory = os.getcwd()
    script = os.path.join(current_directory, 'Data', 'exeRDG.py')

    if platform.system() == "Windows":
        # 백그라운드 분리 실행
        DETACHED = subprocess.CREATE_NEW_PROCESS_GROUP
        process = subprocess.Popen(
            ['python', script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED
        )
    else:
        # Unix 계열: nohup + &
        process = subprocess.Popen(
            ['nohup', 'python', script, '&'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False
        )

    return jsonify({'message': 'RDG.py is running in the background.\nprocessid:'+str(process.pid)}), 200
