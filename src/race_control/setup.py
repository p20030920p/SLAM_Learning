from setuptools import find_packages, setup

package_name = 'race_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='p20030920p',
    maintainer_email='2655113627@qq.com',
    description='Simulation-side velocity adapter: Twist in, TwistStamped out.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'twist_to_twist_stamped = race_control.twist_to_twist_stamped:main',
        ],
    },
)
