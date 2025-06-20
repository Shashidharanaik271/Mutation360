using Mutation360Team11.Constants;
using Mutation360Team11.Services;

namespace Mutation360Team11Test;

public class ExternalServiceTest
{
	[Fact]
	public void GetApplicationName_ShouldReturnCorrectApplicationName()
	{
		// Arrange
		var externalService = new ExternalService();

		// Act
		var result = externalService.GetApplicationName();

		// Assert
		Assert.Equal(ApplicationConstants.ApplicationName, result);
	}
}
