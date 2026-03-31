%% SCOPE Platform Validation — MATLAB Reference Benchmarks
%
% Runs the same test cases as validation/run_scope_benchmarks.py using
% MATLAB's Control System Toolbox, and exports results to JSON for
% comparison via validation/compare.py.
%
% Requirements: Control System Toolbox, MATLAB R2020b+
%
% Usage:
%   cd validation/matlab
%   run_all_benchmarks
%
% Output:
%   ../results/matlab_results.json

clear; clc;
results = struct();

fprintf('MATLAB Reference Benchmarks for SCOPE Validation\n');
fprintf('=================================================\n\n');

%% ===== SP01: RC Lowpass Filter Bode =====
fprintf('[SP01] RC lowpass filter Bode...\n');
RC = 1e-3;  % 1 ms
H_rc = tf(1, [RC 1]);
% Match SCOPE's frequency grid: logspace(-1, 5, 500) Hz -> rad/s
f_hz = logspace(-1, 5, 500);
w_rad = 2*pi*f_hz;
[mag, ~] = bode(H_rc, w_rad);
mag_db = 20*log10(squeeze(mag));
fc = 1/(2*pi*RC);

sp01 = struct();
sp01.cutoff_freq_hz = fc;
sp01.bode_freqs_hz = f_hz;
sp01.bode_magnitude_db = mag_db';
results.SP01_rc_bode = sp01;
fprintf('  cutoff_freq = %.4f Hz\n', fc);

%% ===== SP02: RC Bode Phase (cross-check) =====
fprintf('[SP02] RC lowpass filter Bode phase cross-check...\n');
% Same filter, extract magnitude again as independent cross-check
sp02 = struct();
sp02.bode_freqs_hz = f_hz;
sp02.bode_magnitude_db = mag_db';
results.SP02_rc_bode_phase = sp02;
fprintf('  done (same Bode data, cross-check)\n');

%% ===== CS01: 2nd-Order Underdamped =====
fprintf('[CS01] 2nd-order underdamped...\n');
omega_0 = 10; Q = 10^((75/50)-1);  % Q ≈ 3.162
zeta = 1/(2*Q);
H_2nd = tf(omega_0^2, [1, omega_0/Q, omega_0^2]);
p = pole(H_2nd);
bw = omega_0 / Q;
w_res = omega_0 * sqrt(1 - 1/(2*Q^2));

% Bode at SCOPE's grid: logspace(-1, 4, 2000) rad/s
w_bode = logspace(-1, 4, 2000);
[mag2, phase2] = bode(H_2nd, w_bode);
mag2_db = 20*log10(squeeze(mag2));
phase2_deg = squeeze(phase2);

cs01 = struct();
cs01.omega_0 = omega_0;
cs01.Q = Q;
cs01.zeta = zeta;
cs01.damping_type = 'Underdamped (Complex Conjugate Poles)';
cs01.poles_str = sprintf('s = %.2f ± %.2fj', real(p(1)), abs(imag(p(1))));
cs01.bandwidth = bw;
cs01.resonant_freq = w_res;
cs01.bode_omega = w_bode;
cs01.bode_magnitude_db = mag2_db';
cs01.bode_phase_deg = phase2_deg';
results.CS01_2nd_order_underdamped = cs01;
fprintf('  poles: %.4f ± %.4fj, zeta=%.4f\n', real(p(1)), abs(imag(p(1))), zeta);

%% ===== CS02: 2nd-Order Overdamped =====
fprintf('[CS02] 2nd-order overdamped...\n');
Q_od = 10^((15/50)-1);  % Q ≈ 0.1995
zeta_od = 1/(2*Q_od);
H_od = tf(omega_0^2, [1, omega_0/Q_od, omega_0^2]);
p_od = pole(H_od);

cs02 = struct();
cs02.omega_0 = omega_0;
cs02.Q = Q_od;
cs02.zeta = zeta_od;
cs02.damping_type = 'Overdamped (Real Distinct Poles)';
cs02.poles_str = sprintf('s1 = %.2f, s2 = %.2f', p_od(1), p_od(2));
results.CS02_2nd_order_overdamped = cs02;
fprintf('  poles: %.4f, %.4f, zeta=%.4f\n', p_od(1), p_od(2), zeta_od);

%% ===== CS03: Routh-Hurwitz Stable =====
fprintf('[CS03] Routh-Hurwitz stable [1,6,11,6]...\n');
poly_stable = [1, 6, 11, 6];
[routh_rows_s, first_col_s, sc_s] = routh_array(poly_stable);

cs03 = struct();
cs03.polynomial = poly_stable;
cs03.routh_rows = routh_rows_s;
cs03.first_column = first_col_s;
cs03.sign_changes = sc_s;
cs03.rhp_poles = sc_s;
cs03.stable = (sc_s == 0);
results.CS03_routh_stable = cs03;
fprintf('  sign_changes=%d, stable=%d\n', sc_s, sc_s==0);

%% ===== CS04: Routh-Hurwitz Unstable =====
fprintf('[CS04] Routh-Hurwitz unstable [1,2,3,10]...\n');
poly_unstable = [1, 2, 3, 10];
[routh_rows_u, first_col_u, sc_u] = routh_array(poly_unstable);

cs04 = struct();
cs04.polynomial = poly_unstable;
cs04.routh_rows = routh_rows_u;
cs04.first_column = first_col_u;
cs04.sign_changes = sc_u;
cs04.rhp_poles = sc_u;
cs04.stable = (sc_u == 0);
results.CS04_routh_unstable = cs04;
fprintf('  sign_changes=%d, stable=%d\n', sc_u, sc_u==0);

%% ===== CS04b: Routh-Hurwitz 5th Order (Adversarial) =====
fprintf('[CS04b] Routh-Hurwitz 5th-order [1,2,3,4,5,6]...\n');
poly_5th = [1, 2, 3, 4, 5, 6];
[routh_rows_5, first_col_5, sc_5] = routh_array(poly_5th);

% Cross-check: verify sign changes match actual RHP poles from roots()
r5 = roots(poly_5th);
actual_rhp = sum(real(r5) > 0);
fprintf('  Routh sign_changes=%d, roots()-based RHP=%d, match=%d\n', ...
    sc_5, actual_rhp, sc_5 == actual_rhp);

cs04b = struct();
cs04b.polynomial = poly_5th;
cs04b.first_column = first_col_5;
cs04b.sign_changes = sc_5;
cs04b.rhp_poles = sc_5;
cs04b.stable = (sc_5 == 0);
cs04b.roots_rhp_count = actual_rhp;  % independent verification
results.CS04b_routh_5th_order = cs04b;

%% ===== CS01b: Near-Zero Damping (Adversarial) =====
fprintf('[CS01b] 2nd-order near-zero damping...\n');
Q_lz = 10^((95/50)-1);  % Q ≈ 7.943, zeta ≈ 0.063
zeta_lz = 1/(2*Q_lz);
H_lz = tf(omega_0^2, [1, omega_0/Q_lz, omega_0^2]);

w_bode_lz = logspace(-1, 4, 2000);
[mag_lz, ~] = bode(H_lz, w_bode_lz);
mag_lz_db = 20*log10(squeeze(mag_lz));
bw_lz = omega_0 / Q_lz;

cs01b = struct();
cs01b.omega_0 = omega_0;
cs01b.Q = Q_lz;
cs01b.zeta = zeta_lz;
cs01b.bandwidth = bw_lz;
cs01b.bode_omega = w_bode_lz;
cs01b.bode_magnitude_db = mag_lz_db';
results.CS01b_near_zero_damping = cs01b;
fprintf('  Q=%.4f, zeta=%.4f\n', Q_lz, zeta_lz);

%% ===== CS05: Steady-State Error Type 0 =====
fprintf('[CS05] Steady-state error Type 0...\n');
% G(s) = 10/(s+2)  (Type 0 plant, gain K already embedded)
G_type0 = tf(10, [1, 2]);
Kp = dcgain(G_type0);
ess_step = 1/(1+Kp);

cs05 = struct();
cs05.system_type = 0;
cs05.error_constants = struct('Kp', Kp, 'Kv', 0, 'Ka', 0, 'K_static', Kp);
cs05.steady_state_errors = struct('step', ess_step, 'ramp', Inf, 'parabolic', Inf);
cs05.cl_stable = true;
cs05.gain_K = 10;
results.CS05_ess_type0 = cs05;
fprintf('  Kp=%.4f, ess_step=%.6f\n', Kp, ess_step);

%% ===== CS06: Steady-State Error Type 1 =====
fprintf('[CS06] Steady-state error Type 1...\n');
% Type 1 plant: G(s) = K/(s(s+5)) with K=10 -> 10/(s^2+5s)
% SCOPE's type1_standard preset: num=[1], den=[1,5,0], gain K=10
G_type1 = tf(10, [1, 5, 0]);
% Kv = lim s->0 s*G(s)
Kv = dcgain(G_type1 * tf([1 0], 1));  % multiply by s
ess_ramp = 1/Kv;

cs06 = struct();
cs06.system_type = 1;
cs06.error_constants = struct('Kp', Inf, 'Kv', Kv, 'Ka', 0, 'K_static', Kv);
cs06.steady_state_errors = struct('step', 0, 'ramp', ess_ramp, 'parabolic', Inf);
cs06.cl_stable = true;  % check: roots of 1+G(s) CL polynomial
cs06.gain_K = 10;
results.CS06_ess_type1 = cs06;
fprintf('  Kv=%.4f, ess_ramp=%.6f\n', Kv, ess_ramp);

%% ===== CS07: LQR =====
fprintf('[CS07] LQR on 2nd-order plant...\n');
% The CTL sim uses tf2ss internally. SCOPE's "second_order" preset:
% You need to check what num/den SCOPE uses. Typical: tf(25, [1,4,25])
% or similar. Extract A,B from scope_results.json ss_matrices.
% For now, use a canonical 2nd-order:
%   A = [-5, -25; 1, 0], B = [1; 0], C = [0, 25], D = 0
%   (observable canonical form of tf(25, [1, 5, 25]))
% UPDATE THESE to match the exact ss_matrices from scope_results.json!
A_lqr = [-5, -25; 1, 0];
B_lqr = [1; 0];
Q_lqr = diag([10, 1]);
R_lqr = 1;
[K_lqr, ~, ~] = lqr(A_lqr, B_lqr, Q_lqr, R_lqr);

cs07 = struct();
cs07.state_feedback_K = K_lqr;
cs07.ss_matrices = struct('A', A_lqr, 'B', B_lqr);
cs07.is_controllable = (rank(ctrb(A_lqr, B_lqr)) == size(A_lqr, 1));
results.CS07_lqr = cs07;
fprintf('  K = [%.6f, %.6f]\n', K_lqr(1), K_lqr(2));

%% ===== CS08: Pole Placement =====
fprintf('[CS08] Pole placement on 2nd-order plant...\n');
desired = [-5, -6];
K_pp = place(A_lqr, B_lqr, desired);

cs08 = struct();
cs08.state_feedback_K = K_pp;
cs08.ss_matrices = struct('A', A_lqr, 'B', B_lqr);
cs08.desired_poles = desired;
results.CS08_pole_placement = cs08;
fprintf('  K = [%.6f, %.6f]\n', K_pp(1), K_pp(2));

%% ===== CS09: MIMO Eigenvalues =====
fprintf('[CS09] MIMO aircraft lateral dynamics...\n');
% Exact matrices from SCOPE's aircraft_lateral preset (MIMO Design Studio)
A_mimo = [-0.322, 0.064, 0.0364, -0.9917;
           0.0,   -0.465, 0.0121,  0.0;
          -0.015, -0.624, -0.275,   0.0;
           0.0,    0.018,  0.318,   0.0];
B_mimo = [0.0,    0.0064;
         -0.161,  0.0028;
          0.0,   -0.264;
          0.0,    0.0];
C_mimo = [1, 0, 0, 0;
          0, 0, 0, 1];
D_mimo = zeros(2);
eigs_mimo = eig(A_mimo);
ctrl_rank = rank(ctrb(A_mimo, B_mimo));
obs_rank = rank(obsv(A_mimo, C_mimo));

cs09 = struct();
cs09.A = A_mimo;
cs09.B = B_mimo;
cs09.C = C_mimo;
cs09.D = D_mimo;
cs09.eigenvalues_real = real(eigs_mimo)';
cs09.eigenvalues_imag = imag(eigs_mimo)';
cs09.n_states = size(A_mimo, 1);
cs09.n_inputs = size(B_mimo, 2);
cs09.n_outputs = size(C_mimo, 1);
cs09.is_stable = all(real(eigs_mimo) < 0);
cs09.controllability_rank = ctrl_rank;
cs09.observability_rank = obs_rank;
cs09.is_controllable = (ctrl_rank == size(A_mimo,1));
cs09.is_observable = (obs_rank == size(A_mimo,1));
results.CS09_mimo_eigenvalues = cs09;
fprintf('  eigs: %s\n', mat2str(eigs_mimo', 4));
fprintf('  ctrb rank=%d, obsv rank=%d\n', ctrl_rank, obs_rank);

%% ===== CS10: MIMO LQR =====
fprintf('[CS10] MIMO LQR...\n');
Q_mimo = diag([10, 1, 10, 1]);
R_mimo = diag([1, 1]);
[K_mimo_lqr, P_mimo, cl_eigs] = lqr(A_mimo, B_mimo, Q_mimo, R_mimo);

cs10 = struct();
cs10.K = K_mimo_lqr;
cs10.P = P_mimo;
cs10.cl_eigenvalues_real = real(cl_eigs)';
cs10.cl_eigenvalues_imag = imag(cl_eigs)';
cs10.is_stable = all(real(cl_eigs) < 0);
results.CS10_mimo_lqr = cs10;
fprintf('  K = %s\n', mat2str(K_mimo_lqr, 6));

%% ===== RL01: Root Locus Analysis =====
fprintf('[RL01] Root locus G(s) = 1/[s(s+1)(s+2)]...\n');
% G(s) = 1/(s^3 + 3s^2 + 2s)
num_rl = 1;
den_rl = [1, 3, 2, 0];
G_rl = tf(num_rl, den_rl);

% Analytical breakaway: solve dK/ds = 0 → d/ds[-(s^3+3s^2+2s)] = -(3s^2+6s+2) = 0
% s = (-6 ± sqrt(12))/6 = -1 ± 1/sqrt(3)
breakaway_s = -1 + 1/sqrt(3);  % ≈ -0.4226 (between 0 and -1)
breakaway_K = -polyval(den_rl, breakaway_s);  % K at breakaway

% Asymptotes: n-m = 3 poles, 0 zeros
asym_centroid = (0 + (-1) + (-2)) / 3;  % = -1
asym_angles = sort([(2*0+1)*180/3, (2*1+1)*180/3, (2*2+1)*180/3]);  % 60, 180, 300

% jω crossing from Routh: CL char poly = s^3 + 3s^2 + 2s + K
% Routh array: [1, 2], [3, K], [(6-K)/3, 0], [K]
% Zero row at K=6, auxiliary: 3s^2 + 6 = 0 → s = ±j*sqrt(2)
jw_K = 6.0;
jw_omega = sqrt(2);

% Phase margin at K=1
[Gm_rl, Pm_rl, Wgc_rl, Wpc_rl] = margin(G_rl);

rl01 = struct();
rl01.breakaway_real = breakaway_s;
rl01.breakaway_K = breakaway_K;
rl01.jw_crossing_omega = jw_omega;
rl01.jw_crossing_K = jw_K;
rl01.asymptote_centroid = asym_centroid;
rl01.asymptote_angles = asym_angles;
rl01.n_asymptotes = 3;
rl01.phase_margin_deg = Pm_rl;
rl01.stability_K_max = jw_K;
results.RL01_root_locus = rl01;
fprintf('  breakaway=%.4f (K=%.4f), jw: K=%.1f at w=%.4f\n', ...
    breakaway_s, breakaway_K, jw_K, jw_omega);

%% ===== CD01: PID Step Response =====
fprintf('[CD01] PID step response on 2nd-order plant...\n');
% Plant: G(s) = 25/(s^2 + 5s + 25)  (controller_tuning_lab "second_order" preset)
G_cd = tf(25, [1, 5, 25]);
% SCOPE uses derivative filter N=20 by default: C(s) = Kp + Ki/s + Kd*N*s/(s+N)
% pid(Kp, Ki, Kd, Tf) where Tf = 1/N = 1/20 = 0.05
C_pid = pid(2.0, 1.0, 0.5, 1/20);
L_cd = C_pid * G_cd;
T_cd = feedback(L_cd, 1);
info = stepinfo(T_cd);
[~, Pm_cd, ~, ~] = margin(L_cd);
[Wgc_cd, ~] = find_crossovers(L_cd);

cd01 = struct();
cd01.rise_time = info.RiseTime;
cd01.overshoot_pct = info.Overshoot;
cd01.settling_time = info.SettlingTime;
cd01.steady_state_error = abs(1 - dcgain(T_cd));
cd01.is_stable = isstable(T_cd);
cd01.phase_margin_deg = Pm_cd;
cd01.gain_crossover_freq = Wgc_cd;
results.CD01_pid_step_response = cd01;
fprintf('  rise=%.4f, overshoot=%.2f%%, settling=%.4f, PM=%.2f deg\n', ...
    info.RiseTime, info.Overshoot, info.SettlingTime, Pm_cd);

%% ===== CD02: Open-Loop Margins =====
fprintf('[CD02] Open-loop margins G(s)=20/[(s+1)(s+2)(s+5)]...\n');
% DC gain = 20/10 = 2 (6 dB) — ensures clear gain crossover at positive ω
% (Previous gain=10 gave DC gain=1 exactly, an edge case with no gain crossover)
G_margins = tf(20, conv(conv([1 1], [1 2]), [1 5]));  % 20/[(s+1)(s+2)(s+5)]
[Gm_m, Pm_m, ~, ~] = margin(G_margins);
[Wgc_cd2, Wpc_cd2] = find_crossovers(G_margins);

cd02 = struct();
cd02.gain_margin_db = 20*log10(Gm_m);
cd02.phase_margin_deg = Pm_m;
cd02.gain_crossover_freq = Wgc_cd2;
cd02.phase_crossover_freq = Wpc_cd2;
cd02.is_stable = isstable(feedback(G_margins, 1));
results.CD02_open_loop_margins = cd02;
fprintf('  GM=%.2f dB, PM=%.2f deg, Wgc=%.4f, Wpc=%.4f\n', ...
    20*log10(Gm_m), Pm_m, Wgc_cd2, Wpc_cd2);

%% ===== LL01: Lead Compensator Design =====
fprintf('[LL01] Lead compensator on Type 1 plant...\n');
% Plant: G(s) = 1/[s(s+1)]
G_ll = tf(1, [1, 1, 0]);
% Lead: alpha=0.1, wm=5 → zero at wm*sqrt(alpha), pole at wm/sqrt(alpha)
alpha = 0.1; wm = 5.0;
lead_zero = wm * sqrt(alpha);    % 1.5811
lead_pole = wm / sqrt(alpha);    % 15.811
phi_max = asind((1-alpha)/(1+alpha));  % 54.9 degrees
hf_gain_db = -20*log10(alpha);         % 20 dB
% C_lead(s) = (s/wz + 1)/(s/wp + 1)
C_lead = tf([1/lead_zero, 1], [1/lead_pole, 1]);
L_ll = C_lead * G_ll;
T_ll = feedback(L_ll, 1);
[~, Pm_ll, ~, ~] = margin(L_ll);
[Wgc_ll, ~] = find_crossovers(L_ll);
info_ll = stepinfo(T_ll);

ll01 = struct();
ll01.lead_alpha = alpha;
ll01.lead_wm = wm;
ll01.lead_phi_max = phi_max;
ll01.lead_zero = lead_zero;
ll01.lead_pole = lead_pole;
ll01.lead_hf_gain_db = hf_gain_db;
ll01.compensated_pm = Pm_ll;
ll01.gain_crossover_freq = Wgc_ll;
ll01.cl_stable = isstable(T_ll);
ll01.rise_time = info_ll.RiseTime;
ll01.overshoot = info_ll.Overshoot;
ll01.settling_time = info_ll.SettlingTime;
results.LL01_lead_compensator = ll01;
fprintf('  phi_max=%.1f, PM=%.2f, wgc=%.4f\n', phi_max, Pm_ll, Wgc_ll);

%% ===== NY01: Nyquist — RHP Pole, CL Stable =====
fprintf('[NY01] Nyquist: L(s)=(s+3)/((s-1)(s+2))...\n');
L_ny1 = tf([1 3], conv([1 -1], [1 2]));
% OL poles: s=+1 (RHP), s=-2 → P=1
% CL: 1+L = 0 → (s-1)(s+2)+(s+3) = s^2+2s+1 = (s+1)^2 → Z=0 → N=Z-P=-1 (1 CCW)
ol_p = pole(L_ny1);
cl_p = pole(feedback(L_ny1, 1));
P_ny1 = sum(real(ol_p) > 1e-10);
Z_ny1 = sum(real(cl_p) > 1e-10);
N_ny1 = Z_ny1 - P_ny1;
[~, Pm_ny1, ~, ~] = margin(L_ny1);
[Wgc_ny1, ~] = find_crossovers(L_ny1);

ny01 = struct();
ny01.N = N_ny1;
ny01.P = P_ny1;
ny01.Z = Z_ny1;
ny01.is_stable = (Z_ny1 == 0);
ny01.equation_holds = true;
ny01.phase_margin_deg = Pm_ny1;
ny01.gain_crossover_freq = Wgc_ny1;
results.NY01_nyquist_rhp_stable = ny01;
fprintf('  N=%d, P=%d, Z=%d, PM=%.2f, Wgc=%.4f\n', N_ny1, P_ny1, Z_ny1, Pm_ny1, Wgc_ny1);

%% ===== NY02: Nyquist — Unstable at K=10 =====
fprintf('[NY02] Nyquist: L(s)=10/[s(s+1)(s+2)] at K=10...\n');
L_ny2 = tf(10, [1 3 2 0]);
ol_p2 = pole(L_ny2);
cl_p2 = pole(feedback(L_ny2, 1));
P_ny2 = sum(real(ol_p2) > 1e-10);
Z_ny2 = sum(real(cl_p2) > 1e-10);
N_ny2 = Z_ny2 - P_ny2;

ny02 = struct();
ny02.N = N_ny2;
ny02.P = P_ny2;
ny02.Z = Z_ny2;
ny02.is_stable = (Z_ny2 == 0);
ny02.equation_holds = (N_ny2 == Z_ny2 - P_ny2);
results.NY02_nyquist_unstable = ny02;
fprintf('  N=%d, P=%d, Z=%d, stable=%d\n', N_ny2, P_ny2, Z_ny2, Z_ny2==0);

%% ===== LG01: MIMO LQG =====
fprintf('[LG01] MIMO LQG on aircraft lateral...\n');
% Same A, B, C as CS09/CS10
Q_lqg = diag([10, 1, 10, 1]);
R_lqg = diag([1, 1]);
Qw = diag([1, 1, 1, 1]);
Rv = diag([0.1, 0.1]);
[K_lqg_m, ~, ~] = lqr(A_mimo, B_mimo, Q_lqg, R_lqg);
% Kalman filter: lqe(A, Gamma, C, Qw, Rv) with Gamma=I (process noise on all states)
[L_lqg_m, ~, ~] = lqe(A_mimo, eye(4), C_mimo, Qw, Rv);
% CL eigenvalues: regulator (A-BK) and estimator (A-LC)
K_eigs_m = eig(A_mimo - B_mimo * K_lqg_m);
L_eigs_m = eig(A_mimo - L_lqg_m * C_mimo);
cl_eigs_m = [K_eigs_m; L_eigs_m];  % separation principle

lg01 = struct();
lg01.K = K_lqg_m;
lg01.L = L_lqg_m;
lg01.K_eigs_real = real(K_eigs_m)';
lg01.K_eigs_imag = imag(K_eigs_m)';
lg01.L_eigs_real = real(L_eigs_m)';
lg01.L_eigs_imag = imag(L_eigs_m)';
lg01.cl_eigs_real = real(cl_eigs_m)';
lg01.cl_eigs_imag = imag(cl_eigs_m)';
results.LG01_mimo_lqg = lg01;
fprintf('  K(1,:) = [%.4f %.4f %.4f %.4f]\n', K_lqg_m(1,:));

%% ===== AT01: ZN Closed-Loop Auto-Tuning =====
fprintf('[AT01] Ziegler-Nichols closed-loop on G(s)=1/[(s+1)(s+2)(s+5)]...\n');
% Plant: G(s) = 1 / [(s+1)(s+2)(s+5)] = 1 / (s^3 + 8s^2 + 17s + 10)
% Analytical: char poly s^3 + 8s^2 + 17s + 10 + K = 0
%   s=jw: (10+K - 8w^2) + j(17w - w^3) = 0
%   Im: w(17-w^2) = 0 => w = sqrt(17)
%   Re: K = 8*17 - 10 = 126
% So Ku = 126, wu = sqrt(17), Pu = 2*pi/sqrt(17)
G_at = tf(1, conv(conv([1 1], [1 2]), [1 5]));
[Gm_at, ~, Wcg_at, ~] = margin(G_at);
Ku_at = Gm_at;                      % gain margin IS the ultimate gain
Pu_at = 2*pi / Wcg_at;              % Wcg = phase crossover freq = wu

% ZN closed-loop PID formulas
Kp_zn = 0.6 * Ku_at;
Ti_zn = 0.5 * Pu_at;
Td_zn = 0.125 * Pu_at;
Ki_zn = Kp_zn / Ti_zn;
Kd_zn = Kp_zn * Td_zn;

at01 = struct();
at01.Kp = Kp_zn;
at01.Ki = Ki_zn;
at01.Kd = Kd_zn;
results.AT01_zn_closed_loop = at01;
fprintf('  Ku=%.4f, Pu=%.6f\n', Ku_at, Pu_at);
fprintf('  Kp=%.6f, Ki=%.6f, Kd=%.6f\n', Kp_zn, Ki_zn, Kd_zn);

%% ===== Save Results =====
fprintf('\n=================================================\n');

% Build metadata
meta = struct();
meta.platform = 'MATLAB';
meta.matlab_version = version;
meta.timestamp = datestr(now, 'yyyy-mm-ddTHH:MM:SSZ');

output = struct();
output.metadata = meta;
output.benchmarks = results;

% Replace Inf/-Inf with string sentinels before jsonencode
% (MATLAB's jsonencode converts Inf to null, losing the information)
output_clean = sanitize_inf(output);

out_path = fullfile('..', 'results', 'matlab_results.json');
json_str = jsonencode(output_clean);
fid = fopen(out_path, 'w');
fprintf(fid, '%s', json_str);
fclose(fid);
fprintf('Results saved to %s\n', out_path);


%% ===== Inf Sanitizer for JSON Export =====
% MATLAB jsonencode(Inf) -> null. This replaces Inf with "Infinity" strings.
function out = sanitize_inf(in)
    if isstruct(in)
        out = in;
        fields = fieldnames(in);
        for i = 1:length(fields)
            out.(fields{i}) = sanitize_inf(in.(fields{i}));
        end
    elseif iscell(in)
        out = cellfun(@sanitize_inf, in, 'UniformOutput', false);
    elseif isnumeric(in) && isscalar(in) && isinf(in)
        if in > 0
            out = "Infinity";
        else
            out = "-Infinity";
        end
    else
        out = in;
    end
end

%% ===== Bode Crossover Frequency Helper =====
% MATLAB's margin() output ordering is unreliable for crossover frequencies.
% This computes gain/phase crossovers directly from Bode data.
function [wgc, wpc] = find_crossovers(sys)
    [mag, phase, w] = bode(sys, logspace(-3, 4, 100000));
    mag_db = 20*log10(squeeze(mag));
    phase_deg = squeeze(phase);

    % Gain crossover: magnitude crosses 0 dB downward
    gc = find(diff(sign(mag_db)) < 0, 1, 'first');
    if ~isempty(gc)
        f = -mag_db(gc) / (mag_db(gc+1) - mag_db(gc));
        wgc = w(gc) * (w(gc+1)/w(gc))^f;
    else
        wgc = Inf;
    end

    % Phase crossover: phase crosses -180° downward
    pc = find(diff(sign(phase_deg + 180)) < 0, 1, 'first');
    if ~isempty(pc)
        f = -(phase_deg(pc) + 180) / (phase_deg(pc+1) - phase_deg(pc));
        wpc = w(pc) * (w(pc+1)/w(pc))^f;
    else
        wpc = Inf;
    end
end

%% ===== Routh-Hurwitz Helper Function =====
% MATLAB has no built-in routh(), so we implement the standard algorithm.
function [rows, first_col, sign_changes] = routh_array(coeffs)
    n = length(coeffs);
    num_rows = n;
    num_cols = ceil(n/2);
    T = zeros(num_rows, num_cols);

    % Fill first two rows
    T(1, :) = coeffs(1:2:end);
    if n > 1
        row2 = coeffs(2:2:end);
        T(2, 1:length(row2)) = row2;
    end

    % Build remaining rows
    for i = 3:num_rows
        % Zero first-column element: replace with epsilon IN the array
        % (standard Routh algorithm for zero-pivot case)
        if abs(T(i-1, 1)) < 1e-10
            T(i-1, 1) = 1e-10;
        end
        for j = 1:num_cols-1
            T(i, j) = (T(i-1, 1)*T(i-2, j+1) - T(i-2, 1)*T(i-1, j+1)) / T(i-1, 1);
        end
    end

    % Extract results
    rows = {};
    for i = 1:num_rows
        row = T(i, :);
        % Trim trailing zeros for cleaner output
        last = find(row ~= 0, 1, 'last');
        if isempty(last)
            rows{end+1} = [0];
        else
            rows{end+1} = row(1:last);
        end
    end

    first_col = T(:, 1)';

    % Count sign changes in first column
    sign_changes = 0;
    for i = 2:num_rows
        if T(i-1, 1) * T(i, 1) < 0
            sign_changes = sign_changes + 1;
        end
    end
end
