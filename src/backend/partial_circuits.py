from qiskit import QuantumCircuit
from os import getcwd, path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def display_circuit_of_sub_board(circuit: QuantumCircuit, sub_board_number: int):
    # remove any dangling plots
    plt.close()
    
    # save full circuit to a file
    img_path = path.join(getcwd(), "src", "Images", 'circuit_state.png')

    circuit.draw('mpl', filename=img_path, initial_state=True)
    img = mpimg.imread(img_path)
    plt.close()

    img_cropped = crop_circuit_image(img, sub_board_number)

    fig = plt.figure()
    ax = fig.add_subplot()
    ax.axis("off")
    ax.imshow(img_cropped)
    plt.show(block=False)


def crop_circuit_image(img, sub_board_number: int):
    image_height = img.shape[0]
    
    # slices will overlap a little bit 
    theoretical_height = image_height/9
    slice_height = theoretical_height * 1.5
    slice_half_height = int(slice_height/2)

    # switch from 1-9 numbered to 0-8 indexed, compute slice center
    slice_center = int(theoretical_height * (0.5 + sub_board_number - 1))

    # lower bound is the top of image, upper bound is the bottom
    lower_bound = max(0, slice_center - slice_half_height)
    upper_bound = min(image_height, slice_center + slice_half_height)

    return img[lower_bound:upper_bound, :, :]
        
