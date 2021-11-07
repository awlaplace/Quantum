import matplotlib.pyplot as plt
import numpy as np
import sys

# Qiskit関連のパッケージをインポート
from qiskit import IBMQ, Aer, QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.providers.ibmq import least_busy
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
from qiskit.tools.monitor import job_monitor
from qiskit.circuit.library import MCMT


def main(n, w):
    grover_circuit = QuantumCircuit(n)
    grover_circuit = initialize_s(grover_circuit, list(range(n)))
    grover_circuit.append(oracle(n, w), list(range(n)))
    grover_circuit.append(diffuser(n), list(range(n)))
    grover_circuit.measure_all()
    grover_circuit.draw('mpl')
    backend = Aer.get_backend('qasm_simulator')
    results = execute(grover_circuit, backend=backend, shots=1024).result()
    answer = results.get_counts()
    show_distribution(answer)

    
def initialize_s(qc, qubits):
    """回路のqubitsにHゲートを適用"""
    for q in qubits:
        qc.h(q)

    return qc


def oracle(n, w):
    # オラクルを作成して、回路に実装
    oracle = QuantumCircuit(n)

    bin_w = bin(w)[2:]
    if len(bin_w) < n:
        for _ in range(n - len(bin_w)):
            bin_w.insert(0, 0)

    print(bin_w)

    # w を２進展開した際に，要素が0の箇所をbit反転する
    # 要素が全て1の場合のみに符号を反転させる
    for index in range(len(bin_w)):
        if bin_w[index] == '0':
            oracle.x((n - 1) - index)
    oracle = MCMT('cz', n - 1, 1)
    for index in range(len(bin_w)):
        if bin_w[index] == '0':
            oracle.x((n - 1) - index)

    oracle_gate = oracle.to_gate()
    oracle_gate.name = "U_w"
    
    return oracle_gate


def diffuser(nqubits):
    qc = QuantumCircuit(nqubits)

    # Hゲートで |s> -> |00..0> に変換
    for qubit in range(nqubits):
        qc.h(qubit)
    # Xゲートで |00..0> -> |11..1> に変換
    for qubit in range(nqubits):
        qc.x(qubit)
    # マルチ制御Zゲートをかけます
    qc.h(nqubits-1)
    qc.mct(list(range(nqubits-1)), nqubits-1)  # マルチ制御トフォリ
    qc.h(nqubits-1)
    # |11..1> -> |00..0> に変換
    for qubit in range(nqubits):
        qc.x(qubit)
    # |00..0> -> |s> に変換
    for qubit in range(nqubits):
        qc.h(qubit)

    U_s = qc.to_gate()
    U_s.name = "U_s"
    
    return U_s


# 横軸を整数でプロットする
def show_distribution(answer):
    n = len(answer)
    x = [int(key,2) for key in list(answer.keys())]
    y = list(answer.values())

    fig, ax = plt.subplots()
    rect = ax.bar(x,y)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{:.3f}'.format(height/sum(y)),
                        xy=(rect.get_x()+rect.get_width()/2, height),xytext=(0,0),
                        textcoords="offset points",ha='center', va='bottom')
    autolabel(rect)
    plt.ylabel('Probabilities')
    plt.show()
    fig = plt.figure()
    fig.savefig('grover.png')
    

if __name__ == '__main__':
    args = sys.argv
    n = int(args[1])
    w = int(args[2])
    if w < 2 ** n:
        main(n, w)