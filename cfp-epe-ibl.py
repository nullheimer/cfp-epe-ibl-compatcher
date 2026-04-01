from filecmp import cmp
import os
from pathlib import Path
import re
from shutil import copy
import sys


def main():
	# Paths
	ck3_dir = Path("G:/Steam/steamapps/common/Crusader Kings III")
	output_dir = Path("G:/ck3/cfp-epe-ibl")
	workshop_dir = Path("G:/Steam/steamapps/workshop/content/1158310")
	cfp_epe_dir = Path("C:/Users/Anton/OneDrive/Dokumente/Paradox Interactive/Crusader Kings III/mod/CFP + EPE Compatibility Patch")
	ibl_epe_dir = Path("C:/Users/Anton/OneDrive/Dokumente/Paradox Interactive/Crusader Kings III/mod/IBL + EPE Compatibility Patch")

	# Create path lists for copy operation
	epe_files, cfp_files, ibl_files = [], [], []
	all_paths = (
		(epe_files, "2507209632/common/genes", "epe/epe-genes", "EPE genes"),
		(epe_files, "2507209632/gfx/portraits/portrait_modifiers", "epe/epe-portrait_modifiers", "EPE portraits"),
		(epe_files, "2507209632/common/culture/cultures", "ibl/epe-cultures", "EPE cultures"),
		(cfp_files, "2220098919/common/genes", "cfp/cfp-genes", "CFP genes"),
		(cfp_files, "2220098919/gfx/portraits/portrait_modifiers", "cfp/cfp-portrait_modifiers", "CFP portraits"),
		(ibl_files, "2416949291/common/culture/cultures", "ibl", "IBL cultures")
	)
	additional_headgear_paths = (
		"G:/Steam/steamapps/workshop/content/1158310/2507209632/gfx/portraits/portrait_modifiers", # EPE
		"G:/Steam/steamapps/common/Crusader Kings III/game/gfx/portraits/portrait_modifiers", # Vanilla
		"G:/Steam/steamapps/workshop/content/1158310/2273832430/gfx/portraits/portrait_modifiers", # RICE
		"G:/Steam/steamapps/workshop/content/1158310/2871648329/gfx/portraits/portrait_modifiers" # Unofficial Patch
	)

	# Get current version from ck3 dir, ask for version number and create working directory
	with open(Path(ck3_dir, "titus_branch.txt"), "r", encoding="utf-8") as f:
		fcontent = f.readlines()
	current_version = re.search(r"([\d.]+)", fcontent[0]).group(1)
	
	version_no = input(f"Version number [{current_version}]: ").strip()
	if not version_no:
		version_no = current_version
	else:
		match = None
		match = re.match(r"[\d.]", version_no)
		while match == None:
			version_no = input("Please enter a valid version number: ")
			match = re.match(r"[\d.]", version_no)
	working_dir = create_folders(version_no, output_dir)

	# Scan directories to get list of files to add headgear_2 to
	headgear_files = scan_headgears(working_dir, all_paths, additional_headgear_paths)
	
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
		add_gene(working_dir, all_paths)

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

def scan_headgears(working_dir, all_paths, additional_headgear_paths):
	# We actually need RICE and Unofficial Patch/Vanilla, too
	# version/epe/epe-portrait_modifiers/headgear_2(/additional)
	Path(working_dir, all_paths[1][2], "headgear_2/additional").mkdir(parents=True, exist_ok=True)
	headgear_files = [] # EPE + Vanilla
	
	# Iterate through provided paths and scan directories for files that contain "gene = headgear"
	for path in range(len(additional_headgear_paths)):
		for file in os.listdir(Path(additional_headgear_paths[path])):
			if (
				not re.search(r"custom|.info", file) # Ignore "custom" files
				# Prevent duplicate files from different sources, ...
				and (file not in headgear_files or path == 3) # ... but allow Unofficial Patch nontheless
			):
				with open(Path(additional_headgear_paths[path], file), "r", encoding="utf-8-sig") as f:
					lines = f.readlines()
				for line in lines:
					if re.match(r"^\s*gene\s*=\s*headgear", line):
						headgear_files.append(file)
						# 0th + 1st index of path are EPE and Vanilla
						if path < 2:
							copy(Path(additional_headgear_paths[path], file), Path(working_dir, all_paths[1][2], "headgear_2", file))
						# RICE and Unop files go to a seperate folders, these don't go into CFP + EPE Compatch
						else:
							copy(Path(additional_headgear_paths[path], file), Path(working_dir, all_paths[1][2], "headgear_2/additional", file))
						break

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
	# Manually add EPE cultures
	epe_cultures = [
		"00_berber.txt"
		"00_central_african.txt",
		"00_sahelian_ibl.txt",
		"00_west_african.txt",
		"00_yoruba.txt"
	]
	compatch_files.extend(epe_cultures)
	
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
				# Is the current target a valid directory?
				if os.path.isdir((Path(output_dir, folder, all_paths[i][2]))):
					# Is the file both in the list of mod files and in any of the version folders, newest to oldest?
					if file in all_paths[i][0] and file in os.listdir(Path(output_dir, folder, all_paths[i][2])):
						# Compare both files, if they differ, copy mod file to current working directory
						if cmp(Path(workshop_dir, all_paths[i][1], file), Path(output_dir, folder, all_paths[i][2], file), shallow=False) == False:
							Path(working_dir, all_paths[i][2]).mkdir(parents=True, exist_ok=True)
							copy(Path(workshop_dir, all_paths[i][1], file), Path(working_dir, all_paths[i][2], file))
							operations += 1
						break
		if operations > 0:
			# TODO: Will this add duplicate entries?
			new_dirs.extend([Path(workshop_dir, all_paths[i][1]), Path(working_dir, all_paths[i][2])])
		
		print(f"Copied {operations} files to {all_paths[i][3]} working directory.")

	return new_dirs

def add_gene(working_dir, all_paths):	
	operation_targets = ("headgear_2", "headgear_2/additional")
	for target in operation_targets:
		for file in os.listdir(Path(working_dir, all_paths[1][2], target)):
			if os.path.isfile(Path(working_dir, all_paths[1][2], target, file)):
				with open(Path(working_dir, all_paths[1][2], target, file), "r", encoding="utf-8-sig") as f:
					lines = f.readlines()

				output_lines = []
				headgear_match = False
				indent = ""

				lines_it = iter(lines)
				for line in lines_it:
					# Detect and delete headgear_2 genes from original file
					if re.match(r"^\s*gene\s*=\s*headgear_2\s*$", line):
							# Skip three lines
							i = 0
							while i < 3:
								next(lines_it)
								i += 1
							# Delete partial block already written to output_lines
							try:
								del output_lines[-2:]
							except:
								print("Error deleting headgear_2 gene in add_gene function")
							continue

					if re.match(r"^\s*gene\s*=\s*headgear\s*$", line) and not headgear_match:
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

				# Write result back to the same file
				with open(Path(working_dir, all_paths[1][2], target, file), "w", encoding="utf-8-sig") as f:
					f.writelines("# CFP + EPE: This file was automatically patched by a script to add \"headgear_2\"\n")
					f.writelines(output_lines)

	print("All files processed.")
	return True

if __name__ == "__main__":
	try:
		main()
	finally:
		input("Press enter to exit...")