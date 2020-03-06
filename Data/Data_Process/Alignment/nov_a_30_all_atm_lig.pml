load Temp/nov_a_30_all_atm_lig.pdb
hide all
bg_color white
color blue, chain A
color red, chain B
set transparency=0.2
set sphere_scale, 0.25
set stick_radius, 0.3
show cartoon, chain A
show cartoon, chain B
show stick, HETATM
show spheres, solvent
