# ComparativeCaseStudies
[TuLiP](https://github.com/tulip-control/tulip-control) and Supremica (see below) models for the [paper](https://ieeexplore.ieee.org/document/8795696) titled 'Comparative Case Studies of Reactive Synthesis and Supervisory Control' by [Zahra Ramezani](https://www.chalmers.se/en/staff/Pages/rzahra.aspx), [Jonas Krook](https://www.chalmers.se/en/staff/Pages/krookj.aspx), [Zhennan Fei](https://research.chalmers.se/person/zhennan), [Martin Fabian](https://www.chalmers.se/en/staff/Pages/martin-fabian.aspx) and [Knut Åkesson](https://www.chalmers.se/en/staff/Pages/knut-akesson.aspx).

# Stick-picking game
The stick-picking game is a simple game frequently used to demonstrate concepts of DES and SCT. Two players take turns drawing one, two or three sticks from a pile, initially containing seven sticks. Players are not allowed to skip their turn, and the player who draws the last stick loses the game. 

There is a winning strategy for player one if he or she starts the game by picking 2 sticks. Regardless of the number of sticks now picked by player two, player one can next pick a number of sticks such that only 1 stick remains, offering player two no choice but losing the game.

TuLiP and Supremica models of the stick-picking game are found in the StickPicking folder.

# AD-vehicle
A simplified autonomous driving (AD) model involving two vehicles: an AD vehicle and a manually driven vehicle. The two vehicles are travelling on a circular road with two lanes in the same direction. The problem is to design a controller for the AD-vehicle that at all  times guarantees a safe distance between the two vehicles. That is to say, the AD-vehicle observes the behavior of the manually driven vehicle, and adjusts its own actions accordingly, such that collisions are always avoided.

TuLiP and Supremica models of the AD-example are found in the AutonomousDriving folder.

# Supremica
Supremica.jar, built from the latest snapshot of Supremica, is included in this repository. To launch the Supremica IDE, simply run the following command:
```console
foo@bar:~$ java -Xms512m -Xmx1280m -cp "Supremica.jar" org.supremica.gui.ide.IDE
```
To import the Supremica models used in the case studies of the paper, click File -> Open.

# Licence
Supremica.jar is released under the [Supremica Software License Agreement](https://github.com/krooken/ComparativeCaseStudies/blob/master/LICENCE_SUPREMICA). To other files, GNU GPLv3 applies.
