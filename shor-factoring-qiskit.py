"""
ショアのアルゴリズムをQiskitで実装｜位数発見でN=15を素因数分解する

元記事: https://quantum.yurufuwa.work/learn/shor-factoring-qiskit
ゆるふわ量子コンピュータ (quantum.yurufuwa.work) の解説記事から抜粋したコードです。
"""

import math
import random

N = 15

def pick_a(N):
    a = random.randint(2, N - 1)
    g = math.gcd(a, N)
    if g != 1:
        print(f"a={a} はNと公約数{g}を持つ→運良く量子計算なしで素因数が見つかった！")
        return None
    return a

import numpy as np
from qiskit.circuit.library import UnitaryGate

def build_controlled_U(a_power, N=15, n_qubits=4):
    """|y> -> |a_power * y mod N> を実現する制御ユニタリを作る"""
    dim = 2 ** n_qubits
    perm = np.zeros((dim, dim))
    for y in range(dim):
        if y < N:
            perm[(a_power * y) % N, y] = 1
        else:
            perm[y, y] = 1  # N以上の未使用の状態はそのまま(ユニタリ性を保つため)
    gate = UnitaryGate(perm, label=f"×{a_power} mod {N}")
    return gate.control()

def qft_dagger(n):
    """逆量子フーリエ変換（QFTの記事参照）"""
    qc = QuantumCircuit(n, name="QFT†")
    for qubit in range(n // 2):
        qc.swap(qubit, n - qubit - 1)
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi / float(2 ** (j - m)), m, j)
        qc.h(j)
    return qc

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

n_count = 3   # 精度レジスタ(位数r=4なら3ビットで十分)
N, a = 15, 7

qc = QuantumCircuit(n_count + 4, n_count)
qc.h(range(n_count))     # 精度レジスタを重ね合わせに
qc.x(n_count)            # 標的レジスタを|1>に初期化

for j in range(n_count):
    exponent = pow(a, 2 ** j, N)
    U = build_controlled_U(exponent, N)
    qc.append(U, [j] + list(range(n_count, n_count + 4)))

qc.append(qft_dagger(n_count), range(n_count))
qc.measure(range(n_count), range(n_count))

# 自作のユニタリゲートは、シミュレータが実行できる基本ゲートに変換してから渡す
sim = AerSimulator()
result = sim.run(transpile(qc, sim), shots=2000).result()
counts = result.get_counts()
print(counts)

from fractions import Fraction

measured = "010"   # 例として1つの測定値を取り出す
phase = int(measured, 2) / (2 ** n_count)
frac = Fraction(phase).limit_denominator(N)
r = frac.denominator
print(f"測定値 {measured} → 位相 {phase} → 周期候補 r={r}")

if r % 2 == 0 and pow(a, r // 2, N) != N - 1:
    guesses = [math.gcd(pow(a, r // 2, N) - 1, N),
               math.gcd(pow(a, r // 2, N) + 1, N)]
    print("素因数の候補:", guesses)
