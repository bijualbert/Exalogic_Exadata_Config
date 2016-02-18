
class Test(object):

	staticVar=None;
	instanceVar=None;

	def __init__(self,instanceVar):

		self.instanceVar=instanceVar



test1=Test(10);
Test.staticVar=20;

print test1.instanceVar;
print Test.staticVar;
