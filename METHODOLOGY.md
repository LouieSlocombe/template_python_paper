# Methodology: benzene on graphene and hexagonal boron nitride

This document describes, end to end, how the results of the study are produced: the four
surfaces, the two energy engines, the five computational stages, the analysis behind each
observable, and the software that runs it. Every number quoted here is the literal set in the
corresponding driver under `execution/` or the module under `bghbn/`, so the document and the
code can be checked against each other. Citations are given as bracketed numbers and collected
in the reference list at the end; the machine-readable bibliography is `CITATIONS.bib`.

**Contents**

1. [Scope and systems](#1-scope-and-systems)
2. [Energy and force evaluation](#2-energy-and-force-evaluation)
3. [Structure preparation shared by the stages](#3-structure-preparation-shared-by-the-stages)
4. [Stage 0: plane-wave cutoff and k-point convergence](#4-stage-0-plane-wave-cutoff-and-k-point-convergence)
5. [Stage 1: interfacial friction by Green–Kubo](#5-stage-1-interfacial-friction-by-greenkubo)
6. [Stage 2: benzene-dimer free energy by well-tempered metadynamics](#6-stage-2-benzene-dimer-free-energy-by-well-tempered-metadynamics)
7. [Stage 3: diffusion barriers by climbing-image NEB with a dispersion sweep](#7-stage-3-diffusion-barriers-by-climbing-image-neb-with-a-dispersion-sweep)
8. [Stage 4: surface diffusion coefficients](#8-stage-4-surface-diffusion-coefficients)
9. [Uncertainty, statistics and reporting conventions](#9-uncertainty-statistics-and-reporting-conventions)
10. [Workflow, reproducibility and software](#10-workflow-reproducibility-and-software)
11. [Caveats and provenance notes](#11-caveats-and-provenance-notes)
12. [References](#12-references)

---

## 1. Scope and systems

The study compares the adsorption, lateral diffusion and interfacial friction of benzene
(C₆H₆) on four two-dimensional surfaces: free-standing graphene, free-standing hexagonal boron
nitride (h-BN), and each of them supported on a Ni(111) slab. Five quantities are computed for
every surface:

| Observable | Stage | Engine | Method |
|---|---|---|---|
| Converged plane-wave cutoff and k-mesh | 0 `convergence` | VASP | Total-energy sweeps on the reference cell |
| Interfacial (liquid–solid) friction coefficient λ | 1 `friction` | MACE MD | Green–Kubo force autocorrelation with the Oga finite-size correction |
| Benzene–benzene binding free energy on the surface | 2 `fes` | MACE MD + PLUMED | Well-tempered metadynamics along the ring–ring distance |
| Site-to-site diffusion barrier | 3 `neb` | VASP | Climbing-image NEB, repeated under six dispersion treatments |
| Centre-of-mass diffusion coefficient D | 4 `diffusion` | MACE MD | Mean-squared displacement, Bayesian regression (kinisi) |

### 1.1 Reference cells

The four reference structures are committed in `data/` as ASE trajectory files and are the only
inputs; every stage starts by reading one of them. All four are hexagonal cells (γ = 120°),
periodic in three dimensions, with the slab centred in a vacuum gap of 15 Å along *z* between
periodic images.

| System | File | Atoms | Composition | In-plane cell / Å | Layers |
|---|---|---|---|---|---|
| Graphene | `graphene_monolayer.traj` | 18 | C₁₈ | 7.447 (3×3 of a 2.482 Å primitive cell) | 1 |
| h-BN | `hBN_monolayer.traj` | 18 | B₉N₉ | 7.447 (3×3 of a 2.482 Å primitive cell) | 1 |
| Graphene/Ni(111) | `graphene_Ni.traj` | 49 | C₁₄Ni₃₅ | 6.645 (√7×√7 R19.1°, 7 atoms per layer) | 5 Ni + 1 C |
| h-BN/Ni(111) | `hBN_Ni.traj` | 49 | B₇N₇Ni₃₅ | 6.645 (√7×√7 R19.1°, 7 atoms per layer) | 5 Ni + 1 BN |

In the supported systems the five Ni layers are spaced ≈2.0 Å apart and the overlayer sits
≈2.0 Å above the topmost Ni layer; the overlayer atoms are stored first in the file and the Ni
atoms after them, which is what lets the drivers pick surface sites by index. The in-plane
lattice constants above are those of the committed files; the stages relax the cell in-plane
before use (§3.2), so the production lattice constant is whatever the engine in question gives.

### 1.2 Production supercells

Every production calculation repeats the reference cell 3×3×1. The monolayer supercells are
therefore 162 atoms (≈22.3 Å across) and the Ni-supported ones 441 atoms (≈19.9 Å across),
plus 12 atoms for one benzene or 24 for the dimer. The surfaces lie in the *xy* plane and *z*
is the surface normal throughout.

## 2. Energy and force evaluation

Two engines are used, selected in the package by a single switch
(`bghbn.make_calculator`) so that a driver runs unchanged on either [41].

### 2.1 Machine-learned potential: MACE-MH-1 (stages 1, 2 and 4)

Molecular dynamics, the metadynamics, and the structure preparation for those stages use the
MACE equivariant message-passing potential [10, 11] in its multi-head foundation-model release
MACE-MH-1 [12], evaluated through its ASE calculator (`mace_mp`) with:

- model file `mace-mh-1.model`, head `oc20_usemppbe`, the head trained on PBE-level
  surface–adsorbate data (the Open Catalyst 2020 domain [44]) and intended for surface
  chemistry [12];
- single precision (`float32`), CUDA device, cuEquivariance kernels enabled on the GPU [45];
- an analytical DFT-D3(BJ) dispersion correction [13, 14] with PBE parameters, added on top of
  the MACE energy through torch-dftd [21] with a 40 Bohr cutoff. The driver enables this
  correction whenever a CUDA device is present, which is the case for every production job
  (each MD job requests one GPU); in the CPU fallback path the code turns it off.

### 2.2 Density-functional theory: VASP (stages 0 and 3)

Plane-wave DFT is run with VASP [3, 4] using the projector-augmented-wave method [5, 6] and
the standard PBE PAW data set (`potpaw_PBE.64`, potentials `B`, `C`, `N`, `Ni`) with the
PBE exchange–correlation functional [7]. The settings shared by the ASE-driven runs (stage 3)
are:

| Tag | Value | Notes |
|---|---|---|
| `PREC` | Accurate | `ADDGRID` off (VASP default): the extra augmentation grid is reported to put noise into forces, and the trajectories are read through those forces |
| `ENCUT` | 800 eV | set in the NEB driver; stage 0 is the check on it |
| k-mesh | 3×3×1, Γ-centred | on the 3×3×1 supercell; hexagonal lattices are always sampled Γ-centred |
| `EDIFF` | 10⁻⁶ eV | `NELM` 300, `NELMIN` 5, `ALGO` Normal |
| `LREAL` | Auto | |
| `LASPH` | on | required by the TS/MBD corrections and kept on throughout |
| `ISYM` | 0 | symmetry off: geometries are streamed into one long-lived VASP process and the symmetry detected on the first rarely survives the later ones |
| `ISMEAR` / `SIGMA` | 0 / 0.05 eV | Gaussian smearing for the free-standing sheets |
| Ni-containing cells | `ISPIN` 2, `ISMEAR` 1, `SIGMA` 0.1 eV, `LMAXMIX` 4 | spin-polarised with Methfessel–Paxton smearing [8]; `AMIX_MAG` 0.8, `BMIX_MAG` 10⁻⁴ |
| `MAGMOM` | Ni 0.6 μB, all else 0 | per-element starting moments so the substrate starts ferromagnetic and the closed-shell adsorbate unpolarised |
| mixing | `AMIX` 0.2, `BMIX` 10⁻⁴, `AMIN` 0.01 | |
| `LWAVE`, `LCHARG` | on | kept so a later process in the same directory warm-starts from the converged orbitals |
| `NCORE` | ≤ 8 | one band's plane waves stay inside one shared cache |

Whether a cell is treated as magnetic is decided from its composition (any of Fe, Co, Ni),
so the two Ni-supported systems come out spin-polarised whichever code path builds their
inputs.

**Interactive VASP.** Everything that moves atoms (relaxations, bands) drives VASP through
`vasp-interactive` [22]: one VASP process is kept alive for the whole relaxation and each new
geometry is streamed to it over standard input, so every SCF starts from the orbitals of the
previous step rather than from scratch under a fresh `mpirun`. The package's subclass
(`bghbn.VaspReuse`) additionally makes directory reuse safe: the WAVECAR/CHGCAR left in a run
directory are deleted if the calculation about to start is not the one that wrote them
(different INCAR, KPOINTS or species), and a finished, converged run whose final geometry
(CONTCAR) matches the requested one is read back instead of repeated, which is what makes an
interrupted driver restartable at no cost.

**Dispersion in VASP.** The NEB stage sweeps VASP's built-in van der Waals corrections
through `IVDW`: none, DFT-D2 [15] (`IVDW=1`), DFT-D3 with zero damping [13] (`IVDW=11`),
DFT-D3(BJ) [14] (`IVDW=12`), Tkatchenko–Scheffler [16, 19] (`IVDW=2`) and many-body
dispersion MBD@rsSCS [17, 18, 20] (`IVDW=202`). The short-range damping parameter `VDW_SR` is
pinned to 0.83 for every scheme that reads it, so the sweep varies the dispersion model and
not the damping with it; D3(BJ) is the exception, its Becke–Johnson damping being set through
`VDW_A1`/`VDW_A2`, under which `VDW_SR` is inert. TS with iterative Hirshfeld partitioning and
dDsC are defined in the package but are not part of the production sweep.

## 3. Structure preparation shared by the stages

### 3.1 Geometry optimisation

All relaxations use the BFGS optimiser of ASE [1] on the maximum force component,
`fmax = 0.02 eV/Å` for the MACE stages (1, 2, 4) and `0.01 eV/Å` for the VASP NEB stage. A
relaxation writes its trajectory and BFGS Hessian to disk and resumes from them if rerun,
returning immediately when the last frame already meets the criterion; a trajectory whose
first frame is a different structure is discarded rather than resumed into.

### 3.2 Cell relaxation of the slab

The bare 3×3×1 slab is relaxed with the cell free in-plane, using ASE's
`FrechetCellFilter` (exponential/logarithmic strain parametrisation [1]) under the Voigt
mask `(1, 1, 0, 0, 0, 0)`: the *xx* and *yy* strains relax, while the *zz* component is
frozen so the vacuum gap cannot close under the slab's weak attraction to its own periodic
image, and the shear components are frozen so a hexagonal cell stays hexagonal. Positions and
in-plane lattice constant therefore come from the same engine that runs the subsequent
dynamics or band. For the Ni-supported systems the whole slab (overlayer plus five Ni layers)
relaxes together; no atoms are constrained.

### 3.3 The adsorbate

Benzene is built from ASE's molecule database and relaxed in isolation with the same
calculator and `fmax`. It is placed on the surface by its centre of mass (COM), not by an
atom: the COM is put 5.0 Å above a chosen surface atom (`bghbn.add_adsorbate_by_com`), so a
molecule that is later rotated still starts at the same height. Candidate target atoms are
every non-Ni atom of the supercell, i.e. the overlayer only. The combined slab + benzene system
is then relaxed (positions only) before any dynamics.

### 3.4 Replicas

The two MD-based observables (friction, diffusion) draw their uncertainty from independent
replicas rather than from one long trajectory. For each surface, 20 starting structures are
built by dropping the relaxed benzene onto a surface atom chosen at random from the overlayer
(`random.seed(42)`, one draw per replica), so the ensemble does not share one adsorption
site's bias and the set can be rebuilt exactly. The two stages use the same seed and the
same draw order, so friction replica *k* and diffusion replica *k* start from the same site.

## 4. Stage 0: plane-wave cutoff and k-point convergence

Convergence is tested on the reference cells of §1.1 (not the supercells), as single-point
total energies written and read through pymatgen [2] and run as independent file-based VASP
jobs. The INCAR for these sweeps is `PREC=Accurate`, `ALGO=Normal`, `EDIFF=10⁻⁶ eV`,
`NELM=300`, `LREAL=.FALSE.`, `GGA=PE`, `LASPH`, `ISMEAR=1`, `SIGMA=0.1 eV`, `ISPIN=2`,
`LMAXMIX=4`, the mixing tags of §2.2, no wavefunction or charge output; a cell containing Ni
receives the magnetic settings and per-element `MAGMOM` of §2.2 just before submission.

- **Cutoff sweep.** `ENCUT` from 500 eV to 950 eV in 50 eV steps at a fixed Γ-centred 4×4×1
  mesh, held above the converged mesh so the energies respond to the cutoff alone.
- **k-point sweep.** Meshes with *n* = 3 … 8 points along the direction with the largest
  reciprocal vector, the other in-plane direction scaled in proportion and the vacuum direction
  held at one point (so a slab sweeps as *n*×*n*×1), at a fixed `ENCUT = 800 eV`. Meshes are
  compared through their coarsest k-spacing over the dispersive (non-vacuum) directions, a
  direction counting as vacuum above a 6 Å gap. Γ-centred meshes are forced for hexagonal and
  trigonal lattices, where an offset Monkhorst–Pack mesh [9] would break the symmetry.

The recommendation is read off the data as the coarsest sample from which every finer one
stays within **10⁻³ eV/atom** of the densest, so it is always a sample that was actually run.
Alongside that, the sweep is fitted (exponential or power-law approach to the limit for the
cutoff; power law or damped power-law oscillation in k-spacing for the mesh, the latter for
metallic sweeps that ring rather than approach from one side) and the tolerance solved for
analytically, which can extrapolate past the end of the series and provides the curve drawn
on the figures. The converged primitive-cell mesh is finally mapped onto the 3×3×1 production
supercell by dividing by the repetitions and rounding up, so the supercell is never sampled
more coarsely than the cell it came from. Real-space cutoff-length series in the sense of
kgrid [23] are supported as an alternative to k-point counts.

Each VASP job in this stage runs on one node of 64 MPI ranks with `NCORE = min(8, ranks per
node)`, `KPAR` equal to the node count (dropped, and the Γ-only binary used, for a 1×1×1
mesh), `OMP_NUM_THREADS` set to the cores per rank and `MKL_NUM_THREADS=1` so the maths
library does not nest a second thread pool inside each rank.

## 5. Stage 1: interfacial friction by Green–Kubo

### 5.1 Definition

The friction coefficient λ is the proportionality constant between the lateral force per unit
area that the surface exerts on the adsorbate and the interfacial slip velocity,
λ v_slip = F_wall / A. By linear response it is the time integral of the equilibrium
autocorrelation of that lateral force [24, 25, 26]. For a flat surface in the *xy* plane the
running integral implemented in `bghbn.tools_friction` is

$$
\lambda_{\mathrm{GK}}(t) \;=\; \frac{1}{2\,A\,k_{\mathrm B}T}\int_0^{t}
\big\langle F_x(t')F_x(0) + F_y(t')F_y(0)\big\rangle\,\mathrm{d}t' ,
$$

the factor ½ being the average over the two in-plane directions. F is the net force on the
adsorbate: by Newton's third law it is equal and opposite to the net force the adsorbate
exerts on the surface, and the autocorrelation is blind to the sign, so summing the forces on
the 12 benzene atoms is equivalent to summing them over the slab.

### 5.2 Molecular dynamics protocol

Each of the 20 replicas per surface is run with MACE-MH-1 (§2.1) after the preparation of §3:

| Setting | Value |
|---|---|
| Temperature | 200 K |
| Time step | 0.5 fs |
| Initial velocities | Maxwell–Boltzmann at 200 K, total momentum removed |
| Warm-up | 2 000 steps (1 ps) Langevin [46], friction γ = 0.01 fs⁻¹ (10 ps⁻¹), COM motion not fixed |
| Production | 11 000 steps (5.5 ps) **NVE**, velocity Verlet [47], total momentum removed again at the switch |
| Output | every step, with forces (frame spacing 0.5 fs) |

The production run is microcanonical on purpose. Green–Kubo needs the unperturbed force
autocorrelation, and a Langevin thermostat's random kicks and its own damping term enter the
very forces being correlated; the thermostat is therefore used only to set the temperature,
after which the only forces in the trajectory are physical ones. Every step is written because
the correlation decays on the time scale of a vibration, not of a diffusive hop.

### 5.3 Analysis

1. **Equilibration.** The first 1 000 frames (0.5 ps) of each replica are discarded, leaving
   10 000 frames (5 ps) per replica.
2. **Interfacial area.** A is the van der Waals projection area of the benzene onto the *xy*
   plane: the molecule is rasterised on a 0.05 Å grid with ASE's van der Waals radii and the
   covered pixels counted, so overlapping atoms are not double-counted; a molecule wrapped
   across a periodic boundary is rejoined first. It is evaluated on the last 10 % of frames of
   each replica and averaged over all replicas.
3. **Autocorrelation.** The net in-plane force is autocorrelated by FFT (zero-padded to avoid
   circular wrap-around) with the *unbiased* estimator, each lag τ normalised by the number of
   pairs (N − τ) rather than by N, so replicas of different length can be averaged without a
   length-dependent damping. The mean force is not subtracted (⟨F⟩ = 0 at equilibrium).
4. **Pooling.** The autocorrelation functions of the 20 replicas are averaged *before*
   integration; the average is integrated once (cumulative trapezoid) to λ_GK(t). A single
   short replica barely constrains the fit below, whereas their average constrains it well.
5. **Finite-size correction.** In a finite periodic cell λ_GK(t) does not plateau but decays
   back towards zero (the "plateau problem"), so its peak underestimates λ. Following Oga et al.
   [27], as applied by Thiemann et al. [28], the pooled curve is fitted over the window
   0 ≤ t ≤ t_c with

   $$
   \Lambda(t) = \lambda_0\left(e^{-t/t_1} - e^{-t/t_2}\right),\qquad t_1 > t_2,
   $$

   and the corrected coefficient read off as

   $$
   \lambda = \lambda_0\,\frac{1-u}{1+u},\qquad u = t_2/t_1 .
   $$

   The fit is a bounded least-squares fit (all parameters positive) started from the shape of
   the curve (λ₀ ≈ 1.2 × peak, t₂ ≈ half the time of the peak, t₁ ≈ 2.5 × that). The window
   t_c is fixed at a quarter of the post-equilibration length, 0.25 × 5 ps = **1.25 ps**,
   because the tail of a Green–Kubo curve is noise and letting the fit reach into it biases the
   coefficient. A warning is raised if R² < 0.85 or if t₁ exceeds half the window, in which
   case the correction is poorly constrained.
6. **Uncertainty.** The error bar is a jackknife over replicas [29]: the pooled curve is
   refitted 20 times with one replica left out each time, and the standard error is
   √[(k−1)/k · Σ(λ_i − λ̄)²] over the k leave-one-out values, so the replica-to-replica scatter
   is propagated through the whole non-linear fit rather than through the curve alone.

λ is reported in N s m⁻³ (forces converted from eV/Å, area from Å², time from fs).
Per system the stage writes the curve, the fit and all parameters to `friction.npz`; the
cross-system figure overlays the curves and plots λ ± error for the four surfaces.

## 6. Stage 2: benzene-dimer free energy by well-tempered metadynamics

This stage measures the binding curve of a pair of benzene molecules while both sit on the
surface, using metadynamics [30] in its well-tempered form [31] through PLUMED 2 [32, 33],
coupled to ASE's dynamics via `ase.calculators.plumed`.

**Setup.** Two relaxed benzenes, the second rotated by 30° about *z* and displaced by 7 Å
along −*y* from the first, are relaxed together in isolation, then placed as one unit with
their joint COM 5 Å above the non-Ni surface atom nearest the centre of the relaxed 3×3×1
slab, and the combined system relaxed (MACE-MH-1, `fmax = 0.02 eV/Å`). The two carbon rings
are identified from the bonded graph (ASE neighbour list, connected components) rather than by
index, so the PLUMED selection survives the structure being rebuilt.

**Dynamics.** 200 K, 0.5 fs step, Langevin thermostat with γ = 0.01 fs⁻¹ (10 ps⁻¹) for both a
2 000-step (1 ps) unbiased warm-up and the 100 000-step (50 ps) biased production run.

**Collective variable and bias.** The CV *d* is the distance between the centres of mass of
the two carbon rings, evaluated by PLUMED under the minimum-image convention. Parameters
(PLUMED units set so that energies are in eV, lengths in Å, time in ps):

| Parameter | Value |
|---|---|
| Gaussian width σ | 0.2 Å (about half the unbiased fluctuation of *d*) |
| Initial hill height | 0.01 eV (≈ 0.96 kJ mol⁻¹; the well is only ≈ 0.1 eV deep) |
| Deposition pace | every 200 steps (100 fs) |
| Bias factor | 10 (ΔT = 1 800 K at 200 K) |
| Grid | 0 – 16 Å in 0.01 Å bins |
| Lower wall | harmonic, at 3.0 Å, κ = 5 eV Å⁻² (below the π-stacked minimum near 3.7 Å) |
| Upper wall | harmonic, κ = 5 eV Å⁻², at r_fold − 1.5 Å |
| COLVAR output | every 100 steps |

Because *d* is a minimum-image distance it stops growing once the pair separates past the
Wigner–Seitz boundary of the supercell and folds back towards zero. The fold radius r_fold is
computed for each cell as half the length of the shortest lattice translation (over all 26
neighbouring images), and the upper wall is placed 1.5 Å inside it so the hills only ever see
the physical branch; the lower wall keeps them off the collapsed region. At these settings the
walls cost of order 10 eV to cross.

**Free-energy surface.** After the run, `plumed sum_hills --mintozero` sums the deposited
hills into F(d), written to `fes.dat` with its minimum at zero and plotted in meV against *d*.
The cross-system figure overlays the four curves.

## 7. Stage 3: diffusion barriers by climbing-image NEB with a dispersion sweep

For a physisorbed molecule the barrier to a lateral hop is dominated by dispersion, so the
minimum-energy path is computed under each of the six dispersion treatments of §2.2 and the
schemes compared within and across systems. Each (surface, scheme) pair is one job; a system's
schemes share a directory and are distinguished by a tag.

**End states.** With VASP at the settings of §2.2 (PBE + the scheme in question,
`ENCUT = 800 eV`, 3×3×1 k-mesh, `fmax = 0.01 eV/Å`):

1. the 3×3×1 slab is relaxed with the in-plane cell free (§3.2);
2. benzene is relaxed in isolation;
3. **reactant**: benzene COM 5 Å above surface atom 0, relaxed;
4. **product**: benzene rotated by 30° about the surface normal, COM 5 Å above surface atom 1,
   relaxed.

Atoms 0 and 1 are overlayer atoms of the same species one surface lattice vector
(≈ 2.5 Å) apart (C→C on graphene, B→B on h-BN, and likewise on the supported sheets), so the
hop is a translation between equivalent atop sites combined with a 30° in-plane rotation.
Each end state is relaxed in the run directory of the image it becomes (0 and 8), so the band
starts from their converged wavefunctions.

**Band.** The product is aligned onto the reactant once, up front (on a periodic cell this is
a translation only), so no rigid-body motion is interpolated. A 9-image band (7 movable
images) is built by linear interpolation refined with the image-dependent pair potential
(IDPP) [37], and optimised as a climbing-image NEB [34, 35] with the improved-tangent
estimate [36], spring constant k = 5.0 eV Å⁻², by BFGS to `fmax = 0.01 eV/Å`. Geodesic
interpolation [40] is available in the package but is not used for the production bands.

The band is run image-parallel: ASE evaluates the seven movable images concurrently, each in
its own run directory with its own interactive VASP process that stays alive across the band's
steps, the node's 64 cores being split between them (9 ranks per image). The band trajectory
and Hessian are kept so a band interrupted by the wall clock resumes from its last complete
step rather than restarting.

**Barrier.** Each converged image carries its energy; the barrier is reported as
E_max − E_reactant in meV, and the profiles are drawn against the cumulative path length, one
panel per system with the six schemes overlaid.

## 8. Stage 4: surface diffusion coefficients

### 8.1 Molecular dynamics protocol

The same 20 replicas per surface as §3.4, prepared identically, but run under settings chosen
for a displacement rather than a force autocorrelation:

| Setting | Value |
|---|---|
| Temperature | 200 K |
| Time step | 0.5 fs |
| Thermostat | Langevin [46] throughout, γ = 0.001 fs⁻¹ (1 ps⁻¹), COM motion not fixed |
| Length | 100 000 steps = **50 ps** per replica |
| Output | every 20 steps (frame spacing 10 fs; 5 001 frames per replica) |

A weak thermostat is kept for the production run, unlike stage 1, because a displacement is
insensitive to random forces in a way an autocorrelation is not, while the coupling is ten
times weaker than in the warm-ups so that it does not damp the centre-of-mass motion being
measured. Runs are resumable: a replica cut short by the wall clock continues from its last
written frame with the duplicate opening frame skipped, so the MSD never sees a zero-length
step.

### 8.2 Analysis

The diffusion coefficient is obtained with kinisi ≥ 2.0 [38, 39]:

1. The tracked particle is the mass-weighted centre of mass of the 12 benzene atoms, requested
   through kinisi's molecule interface (`specie=None` with the atom indices and masses).
2. The mean-squared displacement is computed in the surface plane (`dimension="xy"`) with
   kinisi's default drift correction, which subtracts the motion of every other atom, i.e. the
   slab.
3. The MSD is evaluated on **300 geometrically spaced lag times** from one frame (10 fs) up to
   the trajectory length (rounded to whole frames, duplicates removed), which places the points
   evenly on a log–log axis instead of crowding them into the long-lag tail where statistics
   are worst.
4. kinisi models the MSD as a multivariate normal with the analytical covariance of an
   equivalent freely diffusing system, and performs Bayesian linear regression from the start
   of the diffusive regime, **t_diffusive = 10 ps**, with a fixed random state (42). The choice
   of t_diffusive is checked visually on a log–log MSD figure written per system: the diffusive
   regime begins where the gradient flattens to about one.
5. D for each replica is the posterior median, with its 2.5th–97.5th percentile interval; the
   reported value is the **mean over the 20 replicas with the standard deviation across
   replicas** as its uncertainty. Replicas are fitted individually rather than pooled because
   they start at different sites and sample different parts of the surface, so their scatter
   is the uncertainty worth reporting. Units are cm² s⁻¹ as returned by kinisi.

Per system the stage writes the per-replica coefficients and intervals, the MSD curves and
their errors to `diffusion.npz`; the cross-system figure overlays the mean MSDs with their
replica spread and plots D on a logarithmic axis, the scale on which the systems differ.

## 9. Uncertainty, statistics and reporting conventions

- **Friction:** one fit to the replica-averaged autocorrelation; error = jackknife standard
  error over replicas (§5.3). Reported as λ ± σ in 10⁴ N s m⁻³.
- **Diffusion:** one Bayesian fit per replica; value = mean of the 20 medians; error = standard
  deviation over replicas (§8.2). Reported in cm² s⁻¹.
- **Barriers:** deterministic; the spread across the six dispersion schemes is the quantity
  of interest, so no error bar is attached to a single band.
- **Free energies:** a single well-tempered run per system; the surface is shown with its
  minimum at zero.
- **Convergence:** tolerance 10⁻³ eV/atom on the total energy of the reference cell.
- All figures are written through one helper at 600 dpi in PNG and PDF, and systems are
  labelled consistently as Graphene, h-BN, Graphene/Ni(111) and h-BN/Ni(111).

## 10. Workflow, reproducibility and software

**Chain.** Each stage lives under `execution/<N>_<stage>/` as numbered steps with a Slurm
script beside each: a prep step that builds the starting structures and submits the whole
chain, a run step per system (or per replica or per dispersion scheme, as a job array), a
per-system collect queued behind the runs with `--dependency=afterok`, and, where the collect
is per-system, a compare step queued behind every collect. Systems therefore run
concurrently and one that fails takes only itself down. Every output lands under one root
(`$DATA_DIR`): `figures/<stage>/`, `logs/<stage>/` and `<stage>/<system>/` for the raw runs.
The architecture is documented in `WORKFLOW_BLUEPRINT.md`.

**Re-analysis.** The friction and diffusion collects have off-chain twins,
`local_friction.py` and `local_diffusion.py`, which run the identical calculation on any
directory of replica trajectories with the stage's parameters as flag defaults and write beside
the inputs. Both were verified to reproduce the chain step's result file key by key at zero
tolerance on synthetic fixtures with known answers (a filtered-noise force series with a
prescribed biexponential Green–Kubo curve; a rigid two-dimensional random walk with a
prescribed D).

**Seeds.** Replica sites: Python `random.seed(42)`. kinisi posterior sampling:
`random_state=42`. Maxwell–Boltzmann velocities are not seeded and differ between replicas.

**Compute.** MACE MD: one GPU, 32 CPU cores, 24 GB, 4 h per replica job (CUDA 13.0).
VASP: one node, 64 MPI ranks, `MKL_NUM_THREADS=1`, 4 h per band or per sweep point.
PLUMED 2.10.1 with the OPES module compiled in. VASP ≥ 6.4.1 is required for cell relaxation
over the interactive stream.

**Software versions** (development environment at the time of writing; the cluster
environment is built from `build_tools/environment_gpu.yml`):

| Package | Version | Role |
|---|---|---|
| ASE [1] | 3.29.0 | structures, optimisers, MD integrators, NEB, PLUMED and VASP interfaces |
| MACE (`mace-torch`) [10–12] | 0.3.16 | ML potential, model `mace-mh-1` |
| PyTorch | 2.10.0 | MACE backend |
| torch-dftd [21] | 0.5.3 | D3(BJ) correction for MACE |
| vasp-interactive [22] | SMTG-Bham fork | streamed VASP calculator |
| pymatgen [2] | 2026.5.4 | VASP input/output for the convergence sweeps |
| kgrid [23] | 1.2.0 | k-mesh series from cutoff lengths |
| kinisi [38, 39] | 2.0.5 | MSD and Bayesian diffusion coefficients |
| scipp | 26.3.1 | units and arrays under kinisi 2 |
| PLUMED [32, 33] | 2.10.1 | metadynamics |
| NumPy / SciPy / Matplotlib | 2.5.1 / 1.18.0 / 3.11.0 | numerics, FFTs, fitting, figures |
| bghbn [41] | 0.0.1 | this project's package |

## 11. Caveats and provenance notes

- **Finite-size friction.** λ_GK(t) does not plateau in these cells; λ is a fitted, corrected
  quantity and depends on the fit window (1.25 ps) and on the quality of the biexponential
  fit. R² and t₁ relative to the window are printed for every system and should be quoted
  beside λ.
- **Diffusive-regime onset.** D depends materially on t_diffusive; 10 ps is a choice justified
  by the log–log MSD, not a measurement, and should be reported with the value.
- **Dispersion damping.** `VDW_SR = 0.83` is imposed on every VASP scheme that reads it, in
  place of each scheme's own PBE default, so that the sweep isolates the dispersion model. The
  absolute barriers under D2, D3 and TS are therefore not those of the schemes' published
  parametrisations.
- **MACE dispersion on CPU.** The MACE D3(BJ) term is enabled only when a CUDA device is
  found. All production MD jobs request a GPU; a CPU rerun would silently drop dispersion.
- **Cell relaxation history.** Runs produced before 2026-08-07 were generated with no cell
  relaxation (a filter-unwrapping bug in the relaxation helper), at the lattice constants of
  the committed files. Results from before and after that date are not comparable and are not
  mixed in one figure.
- **Ni-supported cells.** The overlayer is commensurate with a √7×√7 R19.1° Ni(111) cell and
  the whole slab, including all five Ni layers, is free to relax; no bottom-layer constraint is
  applied.

## 12. References

1. A. H. Larsen *et al.*, "The atomic simulation environment — a Python library for working
   with atoms", *J. Phys.: Condens. Matter* **29**, 273002 (2017).
   doi:10.1088/1361-648X/aa680e
2. S. P. Ong *et al.*, "Python Materials Genomics (pymatgen): A robust, open-source python
   library for materials analysis", *Comput. Mater. Sci.* **68**, 314–319 (2013).
   doi:10.1016/j.commatsci.2012.10.028
3. G. Kresse and J. Furthmüller, "Efficient iterative schemes for ab initio total-energy
   calculations using a plane-wave basis set", *Phys. Rev. B* **54**, 11169–11186 (1996).
   doi:10.1103/PhysRevB.54.11169
4. G. Kresse and J. Furthmüller, "Efficiency of ab-initio total energy calculations for metals
   and semiconductors using a plane-wave basis set", *Comput. Mater. Sci.* **6**, 15–50
   (1996). doi:10.1016/0927-0256(96)00008-0
5. P. E. Blöchl, "Projector augmented-wave method", *Phys. Rev. B* **50**, 17953–17979
   (1994). doi:10.1103/PhysRevB.50.17953
6. G. Kresse and D. Joubert, "From ultrasoft pseudopotentials to the projector augmented-wave
   method", *Phys. Rev. B* **59**, 1758–1775 (1999). doi:10.1103/PhysRevB.59.1758
7. J. P. Perdew, K. Burke and M. Ernzerhof, "Generalized Gradient Approximation Made Simple",
   *Phys. Rev. Lett.* **77**, 3865–3868 (1996). doi:10.1103/PhysRevLett.77.3865
8. M. Methfessel and A. T. Paxton, "High-precision sampling for Brillouin-zone integration in
   metals", *Phys. Rev. B* **40**, 3616–3621 (1989). doi:10.1103/PhysRevB.40.3616
9. H. J. Monkhorst and J. D. Pack, "Special points for Brillouin-zone integrations",
   *Phys. Rev. B* **13**, 5188–5192 (1976). doi:10.1103/PhysRevB.13.5188
10. I. Batatia, D. P. Kovács, G. N. C. Simm, C. Ortner and G. Csányi, "MACE: Higher Order
    Equivariant Message Passing Neural Networks for Fast and Accurate Force Fields",
    *Advances in Neural Information Processing Systems* **35** (2022). arXiv:2206.07697
11. I. Batatia *et al.*, "A foundation model for atomistic materials chemistry" (2024).
    arXiv:2401.00096
12. I. Batatia, C. Lin, H. Hart, E. Kasoar, A. M. Elena, J. Norwood, T. Wolf and G. Csányi,
    "Cross Learning between Electronic Structure Theories for Unifying Molecular, Surface,
    and Inorganic Crystal Foundation Force Fields" (2025). arXiv:2510.25380. Model release:
    https://github.com/ACEsuit/mace-foundations
13. S. Grimme, J. Antony, S. Ehrlich and H. Krieg, "A consistent and accurate ab initio
    parametrization of density functional dispersion correction (DFT-D) for the 94 elements
    H–Pu", *J. Chem. Phys.* **132**, 154104 (2010). doi:10.1063/1.3382344
14. S. Grimme, S. Ehrlich and L. Goerigk, "Effect of the damping function in dispersion
    corrected density functional theory", *J. Comput. Chem.* **32**, 1456–1465 (2011).
    doi:10.1002/jcc.21759
15. S. Grimme, "Semiempirical GGA-type density functional constructed with a long-range
    dispersion correction", *J. Comput. Chem.* **27**, 1787–1799 (2006).
    doi:10.1002/jcc.20495
16. A. Tkatchenko and M. Scheffler, "Accurate Molecular Van Der Waals Interactions from
    Ground-State Electron Density and Free-Atom Reference Data", *Phys. Rev. Lett.* **102**,
    073005 (2009). doi:10.1103/PhysRevLett.102.073005
17. A. Tkatchenko, R. A. DiStasio Jr., R. Car and M. Scheffler, "Accurate and Efficient Method
    for Many-Body van der Waals Interactions", *Phys. Rev. Lett.* **108**, 236402 (2012).
    doi:10.1103/PhysRevLett.108.236402
18. A. Ambrosetti, A. M. Reilly, R. A. DiStasio Jr. and A. Tkatchenko, "Long-range correlation
    energy calculated from coupled atomic response functions", *J. Chem. Phys.* **140**,
    18A508 (2014). doi:10.1063/1.4865104
19. T. Bučko, S. Lebègue, J. Hafner and J. G. Ángyán, "Tkatchenko-Scheffler van der Waals
    correction method with and without self-consistent screening applied to solids",
    *Phys. Rev. B* **87**, 064110 (2013). doi:10.1103/PhysRevB.87.064110
20. T. Bučko, S. Lebègue, T. Gould and J. G. Ángyán, "Many-body dispersion corrections for
    periodic systems: an efficient reciprocal space implementation", *J. Phys.: Condens.
    Matter* **28**, 045201 (2016). doi:10.1088/0953-8984/28/4/045201
21. torch-dftd: PyTorch implementation of DFT-D2/D3 dispersion corrections, Preferred
    Networks. https://github.com/pfnet-research/torch-dftd
22. vasp-interactive: an ASE calculator for VASP's interactive mode. Original:
    https://github.com/ulissigroup/vasp-interactive ; fork used here:
    https://github.com/SMTG-Bham/vasp-interactive
23. A. J. Jackson, kgrid: k-point meshes from real-space cutoff lengths.
    https://github.com/WMD-group/kgrid
24. M. S. Green, "Markoff Random Processes and the Statistical Mechanics of Time-Dependent
    Phenomena. II. Irreversible Processes in Fluids", *J. Chem. Phys.* **22**, 398–413
    (1954). doi:10.1063/1.1740082
25. R. Kubo, "Statistical-Mechanical Theory of Irreversible Processes. I.", *J. Phys. Soc.
    Jpn.* **12**, 570–586 (1957). doi:10.1143/JPSJ.12.570
26. L. Bocquet and J.-L. Barrat, "Hydrodynamic boundary conditions, correlation functions,
    and Kubo relations for confined fluids", *Phys. Rev. E* **49**, 3079–3092 (1994).
    doi:10.1103/PhysRevE.49.3079
27. H. Oga, Y. Yamaguchi, T. Omori, S. Merabia and L. Joly, "Green-Kubo measurement of
    liquid-solid friction in finite-size systems", *J. Chem. Phys.* **151**, 054502 (2019).
    doi:10.1063/1.5104335
28. F. L. Thiemann, C. Schran, P. Rowe, E. A. Müller and A. Michaelides, "Water Flow in
    Single-Wall Nanotubes: Oxygen Makes It Slip, Hydrogen Makes It Stick", *ACS Nano* **16**,
    10775–10782 (2022). doi:10.1021/acsnano.2c02784
29. B. Efron, *The Jackknife, the Bootstrap and Other Resampling Plans*, SIAM (1982).
    doi:10.1137/1.9781611970319
30. A. Laio and M. Parrinello, "Escaping free-energy minima", *Proc. Natl. Acad. Sci. USA*
    **99**, 12562–12566 (2002). doi:10.1073/pnas.202427399
31. A. Barducci, G. Bussi and M. Parrinello, "Well-Tempered Metadynamics: A Smoothly
    Converging and Tunable Free-Energy Method", *Phys. Rev. Lett.* **100**, 020603 (2008).
    doi:10.1103/PhysRevLett.100.020603
32. G. A. Tribello, M. Bonomi, D. Branduardi, C. Camilloni and G. Bussi, "PLUMED 2: New
    feathers for an old bird", *Comput. Phys. Commun.* **185**, 604–613 (2014).
    doi:10.1016/j.cpc.2013.09.018
33. The PLUMED consortium, "Promoting transparency and reproducibility in enhanced molecular
    simulations", *Nat. Methods* **16**, 670–673 (2019). doi:10.1038/s41592-019-0506-8
34. H. Jónsson, G. Mills and K. W. Jacobsen, "Nudged elastic band method for finding minimum
    energy paths of transitions", in *Classical and Quantum Dynamics in Condensed Phase
    Simulations*, World Scientific, 385–404 (1998). doi:10.1142/9789812839664_0016
35. G. Henkelman, B. P. Uberuaga and H. Jónsson, "A climbing image nudged elastic band method
    for finding saddle points and minimum energy paths", *J. Chem. Phys.* **113**, 9901–9904
    (2000). doi:10.1063/1.1329672
36. G. Henkelman and H. Jónsson, "Improved tangent estimate in the nudged elastic band method
    for finding minimum energy paths and saddle points", *J. Chem. Phys.* **113**, 9978–9985
    (2000). doi:10.1063/1.1323224
37. S. Smidstrup, A. Pedersen, K. Stokbro and H. Jónsson, "Improved initial guess for minimum
    energy path calculations", *J. Chem. Phys.* **140**, 214106 (2014). doi:10.1063/1.4878664
38. A. R. McCluskey, A. G. Squires, J. Dunn, S. W. Coles and B. J. Morgan, "kinisi: Bayesian
    analysis of mass transport from molecular dynamics simulations", *J. Open Source Softw.*
    **9**, 5984 (2024). doi:10.21105/joss.05984
39. A. R. McCluskey, S. W. Coles and B. J. Morgan, "Accurate Estimation of Diffusion
    Coefficients and their Uncertainties from Computer Simulation", *J. Chem. Theory Comput.*
    **21**, 79–87 (2025). doi:10.1021/acs.jctc.4c01249
40. X. Zhu, K. C. Thompson and T. J. Martínez, "Geodesic interpolation for reaction pathways",
    *J. Chem. Phys.* **150**, 164103 (2019). doi:10.1063/1.5090303
41. L. Slocombe, *bghbn: analysis and simulation tools for benzene adsorption, diffusion, and
    friction on graphene and h-BN*, version 0.0.1 (2026), MIT licence.
    https://github.com/LouieSlocombe/paper-benzene-on-graphene-h-BN
42. VASP wiki, "IVDW" and related tags, https://www.vasp.at/wiki/index.php/IVDW (accessed
    September 2026).
43. PLUMED manual, `METAD`, `UPPER_WALLS`, `LOWER_WALLS`, `sum_hills`,
    https://www.plumed.org/doc (accessed September 2026).
44. L. Chanussot *et al.*, "Open Catalyst 2020 (OC20) Dataset and Community Challenges",
    *ACS Catal.* **11**, 6059–6072 (2021). doi:10.1021/acscatal.0c04525
45. NVIDIA cuEquivariance, https://github.com/NVIDIA/cuEquivariance
46. E. Vanden-Eijnden and G. Ciccotti, "Second-order integrators for Langevin equations with
    holonomic constraints", *Chem. Phys. Lett.* **429**, 310–316 (2006).
    doi:10.1016/j.cplett.2006.07.086 (the scheme implemented by ASE's `Langevin`)
47. W. C. Swope, H. C. Andersen, P. H. Berens and K. R. Wilson, "A computer simulation method
    for the calculation of equilibrium constants for the formation of physical clusters of
    molecules: Application to small water clusters", *J. Chem. Phys.* **76**, 637–649 (1982).
    doi:10.1063/1.442716 (velocity Verlet)
