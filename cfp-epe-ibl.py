from filecmp import cmp
import os
from pathlib import Path
import re
from shutil import copy
import sys

def main():
	# Paths
	output_dir = Path("G:/ck3/cfp-epe-ibl")
	workshop_dir = Path("G:/Steam/steamapps/workshop/content/1158310")
	cfp_epe_dir = Path("C:/Users/Anton/OneDrive/Dokumente/Paradox Interactive/Crusader Kings III/mod/CFP + EPE Compatibility Patch")
	ibl_epe_dir = Path("C:/Users/Anton/OneDrive/Dokumente/Paradox Interactive/Crusader Kings III/mod/IBL + EPE Compatibility Patch")

	# Create path lists for copy operation
	epe_files, cfp_files, ibl_files = [], [], []
	all_paths = [
		[epe_files, "2507209632/common/genes", "epe/epe-genes", "EPE genes"],
		[epe_files, "2507209632/gfx/portraits/portrait_modifiers", "epe/epe-portrait_modifiers", "EPE portraits"],
		[cfp_files, "2220098919/common/genes", "cfp/cfp-genes", "CFP genes"],
		[cfp_files, "2220098919/gfx/portraits/portrait_modifiers", "cfp/cfp-portrait_modifiers", "CFP portraits"],
		[ibl_files, "2416949291/common/culture/cultures", "ibl", "IBL"]
	]

	# Ask for version number and create output folder (working directory)
	match = None
	while match == None:
		version_no = input("Version number (e.g. 1.18.3): ").strip()
		match = re.match(r"[\d.]", version_no)
	working_dir = create_folders(version_no, output_dir)

	# Scan EPE dir to get list of files to add headgear_2
	headgear_files = scan_headgears(workshop_dir)
	
	# Get list of compatched files
	populate(cfp_epe_dir, ibl_epe_dir, headgear_files, workshop_dir, all_paths)

	# Compare files with previous version and copy mismatching to working directory
	new_dirs = copy_files(workshop_dir, output_dir, working_dir, all_paths)
	
	# Open directories containing copied files in explorer?
	explorer_prompt = input ("Open working directories? y/[n]: ")
	if explorer_prompt.lower() == "y":
		print("2507209632: EPE\n2220098919: CFP")
		for folder in new_dirs:
			os.startfile(folder)
	
	# Patch files to add headgear_2 gene
	add_gene_prompt = input ("Add headgear_2 genes? [y]/n: ")
	if not add_gene_prompt or add_gene_prompt.lower() == "y":
		add_gene(headgear_files, working_dir, workshop_dir)

def create_folders(version_no, output_dir):
	output_contents = os.listdir(output_dir)
	new_version_no = version_no
	a = 0
	while new_version_no in output_contents:
		# Append
		a += 1
		new_version_no = version_no + "-" + str(a)

	# Create directories
	os.makedirs(Path(output_dir) / new_version_no)
	working_dir = Path(output_dir) / new_version_no

	if new_version_no == version_no:
		print(f"Created {new_version_no}.")
	else:
		print(f"{version_no} already exists, created {new_version_no} instead.")
	return working_dir

def scan_headgears(workshop_dir):
	headgear_files = []
	for file in os.listdir(Path(workshop_dir, "2507209632/gfx/portraits/portrait_modifiers")):
		with open(Path(workshop_dir, "2507209632/gfx/portraits/portrait_modifiers", file), "r", encoding="utf-8-sig") as f:
			lines = f.readlines()
		for line in lines:
			if re.match(r"^\s*gene\s*=\s*headgear", line):
				headgear_files.append(file)
				break

	# Remove "custom" files
	for i in headgear_files:
		if re.search(r"custom", i):
			headgear_files.remove(i)

	return headgear_files

def populate(cfp_epe_dir, ibl_epe_dir, headgear_files, workshop_dir, all_paths):
	# Get list of compatch files
	compatch_files = []

	# CFP + EPE
	for file in os.listdir(Path(cfp_epe_dir, "common/genes")):
		compatch_files.append(file)
	for file in os.listdir(Path(cfp_epe_dir, "gfx/portraits/portrait_modifiers")):
		if file not in headgear_files:
			compatch_files.append(file)
	if not compatch_files:
		input(f"No files were found in {cfp_epe_dir}. Press enter to exit..")
		sys.exit(1)
	
	# IBL + EPE
	tmp = 0
	for file in os.listdir(Path(ibl_epe_dir, "common/culture/cultures")):
		compatch_files.append(file)
		tmp += 1
	if tmp == 0:
		input(f"No files were found in {ibl_epe_dir}. Press enter to exit..")
		sys.exit(1)
	
	# Get list of mod files
	for i in range(len(all_paths)):
		tmp = 0
		for file in os.listdir(Path(workshop_dir, all_paths[i][1])):
			tmp += 1
			if file in compatch_files:
				all_paths[i][0].append(file)
		if tmp == 0:
			current_path = Path(workshop_dir, all_paths[i][1])
			input(f"No {all_paths[i][3]} files were found in {current_path}. Press enter to exit..")
			sys.exit(1)
	
	return True

def copy_files(workshop_dir, output_dir, working_dir, all_paths):
	# Get alphabetically sorted list of versions
	versions = sorted(os.listdir(output_dir), reverse=True)
	if not versions:
		print(f"No folders were found in {output_dir}.")
		return False
	
	# Iterate through version folders and compare first match with workshop file
	new_dirs = []

	for i in range(len(all_paths)):
		operations = 0
		for file in os.listdir(Path(workshop_dir, all_paths[i][1])):
			for folder in versions:
				if os.path.isdir((Path(output_dir, folder, all_paths[i][2]))):
					if file in all_paths[i][0] and file in os.listdir(Path(output_dir, folder, all_paths[i][2])):
						if cmp(Path(workshop_dir, all_paths[i][1], file), Path(output_dir, folder, all_paths[i][2], file), shallow=False) == False:
							Path(working_dir, all_paths[i][2]).mkdir(parents=True, exist_ok=True)
							copy(Path(workshop_dir, all_paths[i][1], file), Path(working_dir, all_paths[i][2], file))
							operations += 1
						break
		if operations > 0:
			new_dirs.extend([Path(workshop_dir, all_paths[i][1]), Path(working_dir, all_paths[i][2])])
		
		print(f"Copied {operations} files to {all_paths[i][3]} working directory.")

	return new_dirs

def add_gene(headgear_files, working_dir, workshop_dir):
	# Copy files from mod to new working directory
	Path(working_dir, "epe/epe-portrait-modifiers/headgear_2").mkdir(parents=True, exist_ok=True)
	for file in headgear_files:
		copy(Path(workshop_dir, "2507209632/gfx/portraits/portrait_modifiers", file), Path(working_dir, "epe/epe-portrait-modifiers/headgear_2", file))
	
	# Perform operation
	for file in os.listdir(Path(working_dir, "epe/epe-portrait-modifiers/headgear_2")):
		with open(Path(working_dir, "epe/epe-portrait-modifiers/headgear_2", file), "r", encoding="utf-8-sig") as f:
			lines = f.readlines()

		output_lines = []
		headgear_match = False
		indent = ""

		for line in lines:
			# Detect headgear
			if headgear_match == False and re.match(r"^\s*gene\s*=\s*headgear\s*$", line):
				headgear_match = True
				output_lines.append(line)
				continue

			# If headgear was found and it's the end of its accessory block 
			if headgear_match and line.strip() == "}":
				# Get indentation
				indent = re.match(r"^(\s*)", line).group(1)
				headgear_match = False
				output_lines.append(line)

				# Add headgear_2 block
				new_block = (
					f"{indent}accessory = {{\n"
					f"{indent}\tmode = add\n"
					f"{indent}\tgene = headgear_2\n"
					f"{indent}\ttemplate = no_headgear\n"
					f"{indent}\tvalue = 0\n"
					f"{indent}}}\n"
				)
				output_lines.append(new_block)
				continue

			output_lines.append(line)
			continue

		output_lines.append(line)

		# Write result back to the same file
		with open(Path(working_dir, "epe/epe-portrait-modifiers/headgear_2", file), "w", encoding="utf-8-sig") as f:
			f.writelines("# CFP + EPE: This file was automatically patched by a script to add \"headgear_2\"\n")
			f.writelines(output_lines)

	print("All files processed.")

if __name__ == "__main__":
	try:
		main()
	finally:
		input("Press enter to exit...")