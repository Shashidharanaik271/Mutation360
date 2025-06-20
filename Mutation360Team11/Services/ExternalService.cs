using Mutation360Team11.Constants;

namespace Mutation360Team11.Services;

public class ExternalService : IExternalService
{
	public string GetApplicationName()
	{
		return ApplicationConstants.ApplicationName;
	}
}
