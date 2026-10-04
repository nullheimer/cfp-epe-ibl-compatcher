from filecmp import cmp
import os
from pathlib import Path
import re
from shutil import copy
import sys


def main():
	# Paths
	script_dir = Path(__file__).parent
	ck3_dir = Path("/mnt/e/SteamLibrary/steamapps/common/Crusader Kings III")
	output_dir = Path(script_dir, "output")
	workshop_dir = Path("/mnt/e/SteamLibrary/steamapps/workshop/content/1158310")
	cfp_epe_dir = Path("/mnt/c/Users/Anton/Documents/Paradox Interactive/Crusader Kings III/mod/CFP + EPE Compatibility Patch")
	ibl_epe_dir = Path("/mnt/c/Users/Anton/Documents/Paradox Interactive/Crusader Kings III/mod/IBL + EPE Compatibility Patch")

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


	# Get current version from ck3 dir, ask for version number and create working directory
	with open(Path(ck3_dir, "launcher/launcher-settings.json"), "r", encoding="utf-8") as f:
			fcontent = f.readlines()
	for line in fcontent:
		if re.match(r".*rawVersion.*", line):
			current_version = re.search(r'^\s*"rawVersion": "(.*)",$', line).group(1)
			break
	
	version_no = input(f"Version number [{current_version}]: ").strip()
	if not version_no:
		version_no = current_version
	else:
		match = None
		#match = re.match(r"[\d.]", version_no)
		while match == None:
			version_no = input("Please enter a valid version number: ")
			match = re.match(r"[\d.]", version_no)
	working_dir = create_folders(version_no, output_dir)
	
	# Get list of compatched files
	populate(cfp_epe_dir, ibl_epe_dir, workshop_dir, all_paths)

	# Compare files with previous version and copy mismatching to working directory
	copy_files(workshop_dir, output_dir, working_dir, all_paths)

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

def populate(cfp_epe_dir, ibl_epe_dir, workshop_dir, all_paths):
	# Get list of compatch files
	compatch_files = []

	# CFP + EPE
	for file in os.listdir(Path(cfp_epe_dir, "common/genes")):
		compatch_files.append(file)
	for file in os.listdir(Path(cfp_epe_dir, "gfx/portraits/portrait_modifiers")):
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
	# Manually add EPE cultures, brute
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


if __name__ == "__main__":
	try:
		main()
	finally:
		input("Press enter to exit...")