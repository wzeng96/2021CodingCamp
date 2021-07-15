# %%
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# %%
def main():

    image = ""
    read_image = np.array(Image.open(image))
    type_read_image = type(read_image)
    read_image_shape = read_image.shape

    plt.imshow(read_image)
    plt.savefig("read_image.png")
    
    xlen = read_image_shape[0]
    ylen = read_image_shape[1]


    print(read_image_shape)
    print(xlen)
    print(ylen)

    new_figure = np.zeros(read_image_shape)

    for i in range(xlen):
        for j in range(ylen):
            pixel_value = read_image[i, j, :]
            if pixel_value > 4000:
                new_figure[i, j] = pixel_value + 3000
            else:
                new_figure[i,j] = pixel_value
    

    # new_figure[read_image > 4000] = read_image[read_image > 4000] + 3000
    # new_figure[read_image <= 4000] = read_image[read_image <= 4000]




    plt.imshow(new_figure)
    plt.savefig("newfigure.png")


main()