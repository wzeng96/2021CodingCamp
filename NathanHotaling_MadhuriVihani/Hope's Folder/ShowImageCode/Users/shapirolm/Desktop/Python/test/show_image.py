# %%
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
image_file = r"C:/Users/shapirolm/Desktop/Python/test/png image.png"
img = mpimg.imread(image_file)
print(type(img))
print(img.dtype)
plt.imshow(img)
plt.show()
