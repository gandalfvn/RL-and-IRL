# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <headingcell level=2>

# Misc.

# <headingcell level=3>

# Pythonesque stuff

# <codecell>

#!/usr/bin/env python
from random import choice
from pylab import *
from mpl_toolkits.mplot3d import axes3d, Axes3D

def non_scalar_vectorize(func, input_shape, output_shape):
    """Return a featurized version of func, where func takes a potentially matricial argument and returns a potentially matricial answer.

    These functions can not be naively vectorized by numpy's vectorize.
 
    With vfunc = non_scalar_vectorize( func, (2,), (10,1) ),
    
    func([p,s]) will return a 2D matrix of shape (10,1).

    func([[p1,s1],...,[pn,sn]]) will return a 3D matrix of shape (n,10,1).

    And so on.
    """
    def vectorized_func(arg):
        #print 'Vectorized : arg = '+str(arg)
        nbinputs = prod(arg.shape)/prod(input_shape)
        if nbinputs == 1:
            return func(arg)
        outer_shape = arg.shape[:len(arg.shape)-len(input_shape)]
        outer_shape = outer_shape if outer_shape else (1,)
        arg = arg.reshape((nbinputs,)+input_shape)
        answers=[]
        for input_matrix in arg:
            answers.append(func(input_matrix))
        return array(answers).reshape(outer_shape+output_shape)
    return vectorized_func

def zip_stack(*args):
    """Given matrices of same shape, return a matrix whose elements are tuples from the arguments (i.e. with one more dimension).

    zip_stacking three matrices of shape (n,p) will yeld a matrix of shape (n,p,3)
    """
    shape = args[0].shape
    nargs = len(args)
    args = [m.reshape(-1) for m in args]
    return array(zip(*args)).reshape(shape+(nargs,))
#zip_stack(array([[1,2,3],[4,5,6]]),rand(2,3))

# <headingcell level=3>

# General Mathematics code

# <codecell>

class GradientDescent(object):
    
   def alpha( self, t ):
      raise NotImplementedError, "Cannot call abstract method"

   theta_0=None
   Threshold=None
   T = -1
   sign = None
        
   def run( self, f_grad, f_proj=None, b_norm=False ): #grad is a function of theta
      theta = self.theta_0.copy()
      best_theta = theta.copy()
      best_norm = float("inf")
      best_iter = 0
      t=0
      while True:#Do...while loop
         t+=1
         DeltaTheta = f_grad( theta )
         current_norm = norm( DeltaTheta )
         if b_norm and  current_norm > 0.:
             DeltaTheta /= norm( DeltaTheta )
         theta = theta + self.sign * self.alpha( t )*DeltaTheta
         if f_proj:
             theta = f_proj( theta )
         print "Norme du gradient : "+str(current_norm)+", pas : "+str(self.alpha(t))+", iteration : "+str(t)

         if current_norm < best_norm:
             best_norm = current_norm
             best_theta = theta.copy()
             best_iter = t
         if norm < self.Threshold or (self.T != -1 and t >= self.T):
             break

      print "Gradient de norme : "+str(best_norm)+", a l'iteration : "+str(best_iter)
      return best_theta

# <codecell>

class StructuredClassifier(GradientDescent):
    sign=-1.
    Threshold=0.1 #Sensible default
    T=40 #Sensible default
    phi=None
    phi_xy=None
    inputs=None
    labels=None
    label_set=None
    dic_data={}
    x_dim=None
    
    def alpha(self, t):
        return 3./(t+1)#Sensible default
    
    def __init__(self, data, x_dim, phi, phi_dim, Y):
        self.x_dim=x_dim
        self.inputs = data[:,:-1]
        shape = list(data.shape)
        shape[-1] = 1
        self.labels = data[:,-1].reshape(shape)
        self.phi=phi
        self.label_set = Y
        self.theta_0 = zeros((phi_dim,1))
        self.phi_xy = self.phi(data)
        for x,y in zip(self.inputs,self.labels):
            self.dic_data[str(x)] = y
        print self.inputs.shape
    
    def structure(self, xy):
        return 0. if xy[-1] == self.dic_data[str(xy[:-1])] else 1.
        
    def structured_decision(self, theta):
        def decision( x ):
            score = lambda xy: dot(theta.transpose(),self.phi(xy)) + self.structure(xy)
            input_label_couples = [hstack([x,y]) for y in self.label_set]
            best_label = argmax(input_label_couples, score)[-1]
            return best_label
        vdecision = non_scalar_vectorize(decision, (self.x_dim,), (1,1))
        return lambda x: vdecision(x).reshape(x.shape[:-1]+(1,))
    
    def gradient(self, theta):
        classif_rule = self.structured_decision(theta)
        y_star = classif_rule(self.inputs)
        #print "Gradient : "+str(y_star)
        #print str(self.labels)
        phi_star = self.phi(hstack([self.inputs,y_star]))
        return mean(phi_star-self.phi_xy,axis=0)
    
    def run(self):
        f_grad = lambda theta: self.gradient(theta)
        theta = super(StructuredClassifier,self).run( f_grad, b_norm=True)
        classif_rule = greedy_policy(theta,self.phi,self.label_set)
        return classif_rule,theta
        

# <codecell>

def least_squares_regressor(data, psi, x_dim, _lambda=0.1):
    """Return a function that given a x, will output a y based on a least square regression of the data provided in argument"""
    X = data[:,0:x_dim]
    Y = data[:,x_dim:]
    psi_X = squeeze(psi(X))
    #print psi_X
    omega = dot(dot(inv(dot(psi_X.transpose(),psi_X)+_lambda*identity(psi_X.shape[1])),psi_X.transpose()),Y)
    #omega = dot(inv(dot(psi_X.transpose(),psi_X)+_lambda*identity(psi_X.shape[1])),psi_X.transpose())
    #omega = inv(dot(psi_X.transpose(),psi_X)+_lambda*identity(psi_X.shape[1]))
    #omega = dot(psi_X.transpose(),psi_X)+_lambda*identity(psi_X.shape[1])
    #print psi_X.shape
    #omega = dot(psi_X.transpose(),psi_X)
    regression = lambda x:dot(omega.transpose(),psi(x))
    return regression
                

# <headingcell level=2>

# Inverted Pendulum-specific code

# <codecell>

RANDOM_RUN_LENGTH=10000
EXPERT_RUN_LENGTH=3000
TRANS_WIDTH=6
ACTION_SPACE=[0,1,2]
GAMMA=0.9 #Discout factor
LAMBDA=0.1 #Regularization coeff for LSTDQ

# <codecell>

def inverted_pendulum_single_psi( state ):
    position,speed=state
    answer = zeros((10,1))
    index = 0
    answer[index] = 1.
    index+=1
    for i in linspace(-pi/4,pi/4,3):
        for j in linspace(-1,1,3):
            answer[index] = exp(-(pow(position-i,2) +
                                  pow(speed-j,2))/2.)
            index+=1
    #print "psi stops ar index "+str(index)
    return answer

inverted_pendulum_psi = non_scalar_vectorize( inverted_pendulum_single_psi,(2,), (10,1) )

#[inverted_pendulum_psi(rand(2)).shape,
# inverted_pendulum_psi(rand(2,2)).shape,
# inverted_pendulum_psi(rand(3,5,2)).shape]

# <codecell>

def inverted_pendulum_single_phi(state_action):
    position, speed, action = state_action
    answer = zeros((30,1))
    index = action*10
    answer[ index:index+10 ] = inverted_pendulum_single_psi( [position, speed] )
    return answer

inverted_pendulum_phi = non_scalar_vectorize(inverted_pendulum_single_phi, (3,), (30,1))

#[inverted_pendulum_phi(rand(3)).shape,
# inverted_pendulum_phi(rand(3,3)).shape,
# inverted_pendulum_phi(rand(4,5,3)).shape]

# <codecell>

def inverted_pendulum_V(omega):
    policy = greedy_policy( omega, inverted_pendulum_phi, ACTION_SPACE )
    def V(pos,speed):
        actions = policy(zip_stack(pos,speed))
        Phi=inverted_pendulum_phi(zip_stack(pos,speed,actions))
        return squeeze(dot(omega.transpose(),Phi))
    return V

# <codecell>

def inverted_pendulum_next_state(state, action):
    position,speed = state
    noise = rand()*20.-10.
    control = None
    if action == 0:
        control = -50 + noise;
    elif action == 1:
        control = 0 + noise;
    else: #action==2
        control = 50 + noise;
    g = 9.8;
    m = 2.0;
    M = 8.0;
    l = 0.50;
    alpha = 1./(m+M);
    step = 0.1;
    acceleration = (g*sin(position) - 
                    alpha*m*l*pow(speed,2)*sin(2*position)/2. - 
                    alpha*cos(position)*control) / (4.*l/3. - alpha*m*l*pow(cos(position),2))
    next_position = position +speed*step;
    next_speed = speed + acceleration*step;
    return array([next_position,next_speed])

def inverted_pendulum_reward( state ):
    position,speed = state
    if abs(position)>pi/2.:
        return -1.
    return 0.

def inverted_pendulum_uniform_initial_state():
    return (rand(2)*2.-1.)*pi/2.

def inverted_pendulum_optimal_initial_state():
    return rand(2)*0.2-0.1

def inverted_pendulum_trace( pi,run_length=RANDOM_RUN_LENGTH,
                             initial_state=inverted_pendulum_optimal_initial_state ):
    data = zeros((run_length, TRANS_WIDTH))
    state = initial_state()
    for i,void in enumerate( data ):
        action = pi( state )
        new_state = inverted_pendulum_next_state( state, action )
        reward = inverted_pendulum_reward( new_state )
        data[i,:] = hstack([state,action,new_state,[reward]])
        if reward == 0.:
            state = new_state
        else: #Pendulum has fallen
            state = initial_state()
    return data

def inverted_pendulum_random_trace():
    pi = lambda s: choice(ACTION_SPACE)
    return inverted_pendulum_trace( pi )

def inverted_pendulum_expert_trace():
    data = inverted_pendulum_random_trace()
    policy,omega = lspi( data, s_dim=2,a_dim=1, A=ACTION_SPACE, phi=inverted_pendulum_phi, phi_dim=30 )
    inverted_pendulum_plot(inverted_pendulum_V(omega))
    two_args_pol = lambda p,s:squeeze(policy(zip_stack(p,s)))
    inverted_pendulum_plot(two_args_pol,contour_levels=3)
    return inverted_pendulum_trace( policy,run_length=EXPERT_RUN_LENGTH ),policy

# <codecell>

def inverted_pendulum_plot( f, draw_contour=True, contour_levels=50, draw_surface=False ):
    '''Display a surface plot of function f over the state space'''
    pos = linspace(-pi,pi,30)
    speed = linspace(-pi,pi,30)
    pos,speed = meshgrid(pos,speed)
    Z = f(pos,speed)
    fig = figure()
    if draw_surface:
        ax=Axes3D(fig)
        ax.plot_surface(pos,speed,Z)
    if draw_contour:
        contourf(pos,speed,Z,levels=linspace(min(Z.reshape(-1)),max(Z.reshape(-1)),contour_levels+1))
        colorbar()
    show()
def inverted_pendulum_plot_policy( policy ):
    two_args_pol = lambda p,s:squeeze(policy(zip_stack(p,s)))
    inverted_pendulum_plot(two_args_pol,contour_levels=3)
#test_omega=zeros((30,1))
#test_omega[5]=1.
#inverted_pendulum_plot(inverted_pendulum_V(test_omega))
#pol = greedy_policy(test_omega,inverted_pendulum_phi,ACTION_SPACE)
#inverted_pendulum_plot_policy(policy_good)

# <headingcell level=2>

# Reinforcement Learning Code

# <codecell>

def argmax( set, func ):
     return max( zip( set, map(func,set) ), key=lambda x:x[1] )[0]

def greedy_policy( omega, phi, A ): 
    def policy( *args ):
        state_actions = [hstack(args+(a,)) for a in A]
        q_value = lambda sa: float(dot(omega.transpose(),phi(sa)))
        best_action = argmax( state_actions, q_value )[-1] #FIXME6: does not work for multi dimensional actions
        return best_action
    vpolicy = non_scalar_vectorize( policy, (2,), (1,1) )
    return lambda state: vpolicy(state).reshape(state.shape[:-1]+(1,))

#test_omega=zeros((30,1))
#test_omega[1]=1.
#pol = greedy_policy( test_omega, inverted_pendulum_phi, ACTION_SPACE )
#[pol(rand(2)),pol(rand(3,2)).shape,pol(rand(3,3,2)).shape]

# <codecell>

def lstdq(phi_sa, phi_sa_dash, rewards, phi_dim=1):
    #print "shapes of phi de sa, phi de sprim a prim, rewards"+str(phi_sa.shape)+str(phi_sa_dash.shape)+str(rewards.shape)
    A = zeros((phi_dim,phi_dim))
    b = zeros((phi_dim,1))
    for phi_t,phi_t_dash,reward in zip(phi_sa,phi_sa_dash,rewards):
        A = A + dot( phi_t,
                     (phi_t - GAMMA*phi_t_dash).transpose())
        b = b + phi_t*reward
    return dot(inv(A + LAMBDA*identity( phi_dim )),b)

def lspi( data, s_dim=1, a_dim=1, A = [0], phi=None, phi_dim=1, epsilon=0.01, iterations_max=30,
          plot_func=None):
    nb_iterations=0
    sa = data[:,0:s_dim+a_dim]
    phi_sa = phi(sa)
    s_dash = data[:,s_dim+a_dim:s_dim+a_dim+s_dim]
    rewards = data[:,s_dim+a_dim+s_dim]
    omega = zeros(( phi_dim, 1 ))
    #omega = genfromtxt("../Code/InvertedPendulum/omega_E.mat").reshape(30,1)
    diff = float("inf")
    cont = True
    policy = greedy_policy( omega, phi, A )
    while cont:
        if plot_func:
            plot_func(omega)
        sa_dash = hstack([s_dash,policy(s_dash)])
        phi_sa_dash = phi(sa_dash)
        omega_dash = lstdq(phi_sa, phi_sa_dash, rewards, phi_dim=phi_dim)
        diff = norm( omega_dash-omega )
        omega = omega_dash
        policy = greedy_policy( omega, phi, A )
        nb_iterations+=1
        print "LSPI, iter :"+str(nb_iterations)+", diff : "+str(diff)
        if nb_iterations > iterations_max or diff < epsilon:
            cont = False
    return policy,omega

# <headingcell level=2>

# Inverse Reinforcement Learning code

# <codecell>

def CSI(data, classifier, regressor, A, s_dim=1, gamma=0.9, a_dim=1):
    s = data[:,0:s_dim]
    a = data[:,s_dim:s_dim+a_dim]
    s_dash = data[:,s_dim+a_dim:s_dim+a_dim+s_dim]
    pi_c,q = classifier(hstack([s,a]))
    a_dash = pi_c(s_dash)
    hat_r = q(data[:,0:s_dim+a_dim])-gamma*q(hstack([s_dash,a_dash]))
    
    r_min = min(hat_r)-1.*ones(hat_r.shape)
    regression_input_matrices = [hstack([s,action*ones(hat_r.shape)]) for action in A] #FIXME7: may not work for vectorial actions
    def add_output_column( reg_mat ):
        actions = reg_mat[:,-a_dim:]
        hat_r_bool_table = actions==a
        r_min_bool_table = not hat_r_bool_table
        output_column = hat_r_bool_table*hat_r+r_min_bool_table*r_min
        return hstack([reg_mat,output_column])
    regression_matrix = vstack(map(add_output_column,regression_input_matrices))
    return regressor( regression_matrix )
    

# <codecell>

def get_structured_classifier_for_SCI(s_dim, phi, phi_dim, A):
    """Return a classifier function as expected by the CSI algorithm using the StructuredClassifier class"""
    def classifier(data):
        structured_classifier = StructuredClassifier(data, s_dim, phi, phi_dim, A)
        classif_rule,omega_classif = structured_classifier.run()
        score = lambda sa: squeeze(dot(omega_classif.transpose(),phi(sa)))
        return classif_rule,score
    return classifier

def get_least_squares_regressor_for_SCI(psi, s_dim):
    #ax=b,find x
    def regressor(data):
        a=squeeze(psi(data[:,0:s_dim]))
        b=data[:,s_dim:]
        x=lstsq(a,b)[0]
        return lambda s:dot(x.transpose(),psi(s))
    return lambda data: regressor(data)

# <headingcell level=2>

# Experiment 1 Code

# <codecell>

            
#data_random = inverted_pendulum_random_trace()
data_expert,policy = inverted_pendulum_expert_trace()
#random_falls_rate = - mean( data_random[:,5] )
expert_falls_rate = - mean( data_expert[:,5] )
#print "Rate of falls for random controller "+str(random_falls_rate)
print "Rate of falls for expert controller "+str(expert_falls_rate)
#reward = cascading_irl( data_expert )
#value_function = lspi( reward, data_random )
#inverted_pendulum_plot( reward, "Reward.pdf" )
#inverted_pendulum_plot( value_function, "ValueFunction.pdf" )
#sum(data_random[:,5])
#plot(data_random[:,0],data_random[:,1],ls='',marker='o')

# <codecell>

states = rand(1000,2)*6-3
actions = policy(states)
data = hstack([states,actions])
classifier = get_structured_classifier_for_SCI(2, inverted_pendulum_phi, 30, ACTION_SPACE)
classif_rule,score = classifier(data)
data_0 = array([l for l in data if l[2]==0.])
data_1 = array([l for l in data if l[2]==1.])
data_2 = array([l for l in data if l[2]==2.])
inverted_pendulum_plot_policy(policy)
plot(data_0[:,0],data_0[:,1],ls='',marker='o')
plot(data_1[:,0],data_1[:,1],ls='',marker='o')
plot(data_2[:,0],data_2[:,1],ls='',marker='o')
inverted_pendulum_plot_policy( classif_rule )
two_args_score = lambda p,s: score(zip_stack(p,s,squeeze(classif_rule(zip_stack(p,s)))))
inverted_pendulum_plot(two_args_score)

# <codecell>

reg_X = rand(1000,2)*2-1
test_theta = rand(10,1)-0.5
reg_Y = dot(test_theta.transpose(),inverted_pendulum_psi(reg_X)).reshape(1000,1)

regressor = get_least_squares_regressor_for_SCI(inverted_pendulum_psi, 2)
reg = regressor(hstack([reg_X,reg_Y]))

X = linspace(-1,1,30)
Y = X
X,Y = meshgrid(X,Y)
XY=zip_stack(X,Y)
Z = squeeze(reg(XY))
true_Z = squeeze(reg(XY))

from matplotlib import cm
fig = figure()
ax=Axes3D(fig)
ax.plot_surface(X,Y,Z, cmap=cm.jet,cstride=1,rstride=1)
ax.scatter(reg_X[:,0],reg_X[:,1],reg_Y,c=reg_Y)
show()
