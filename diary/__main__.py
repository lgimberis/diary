from pathlib import Path

import diary

def main():
    # Check for config files in home directory
    config_directory = Path.home() / '.diary'
    config_directory.mkdir(exist_ok=True)

    config_file = config_directory / 'config.cfg'
    if not config_file.is_file():
        # Create config file
        print("No config file found.")
        print("Where do you want Diary to store its data?")
        storage_location = Path(input("Storage location: "))
        print("Do you prefer GUI or Console mode?")
        gui_preference = ""
        while gui_preference.upper() not in ["GUI", "CONSOLE"]:
            if gui_preference:
                print("Please try again, only the values 'GUI' or 'Console' are accepted.")
            gui_preference = input("Preference (GUI or Console)")
        with open(config_file, mode='w') as f:
            f.write(f"Storage={storage_location}\n")
            f.write(f"Mode={gui_preference}")
    else:
        # Grab preferences from config file
        with open(config_file, mode='r') as f:
            storage_line = f.readline()
            storage_location = Path(storage_line.split('=')[1].strip())
            gui_line = f.readline()
            gui_preference = gui_line.split('=')[1].strip()

    storage_location = storage_location.expanduser()
    if gui_preference == 'GUI':
        diary.diary_gui.run(storage_location)
    else:
        diary.diary_console.run(storage_location)

        
if __name__ == "__main__":
    main()
