using Mutation360Team11.Dtos;
using Mutation360Team11.Models;

namespace Mutation360Team11.Services;
  
public class AccountService
{
	private readonly IExternalService _externalService;

	public AccountService(IExternalService externalService)
	{
		_externalService = externalService;
	}

	public List<AccountDetailsDto> GetAllAccountDescription(List<Account> accounts, bool canProcessAccountDescription)
	{
		List<AccountDetailsDto> accountDetails = accounts.Select(
			ad => new AccountDetailsDto
			{
				AccountName = ad.AccountName,
				AccountDescription = canProcessAccountDescription ? ad.AccountDescription! : null!
			}).ToList();

		return accountDetails;
	}

	public List<AccountTypeAndDescriptionDetailsDto> GetAllAccountTypeAndDescription(List<Account> accounts)
	{
		List<AccountTypeAndDescriptionDetailsDto> accountDetails = accounts.Select(
			ad => new AccountTypeAndDescriptionDetailsDto
			{
				AccountDescription = ad.AccountDescription!,
				AccountType = ad.AccountType
			}).ToList();

		return accountDetails;
	}

	public string GetAccountKeySecondElement(string accountKey)
	{
		return accountKey != null! ? accountKey.Split(":").Skip(1).First() : null!;
	}

	public string GetAccountIdByOtherInformationAsString(string name, string description, string key)
	{
		if (string.IsNullOrWhiteSpace(name) || string.IsNullOrWhiteSpace(description) ||
			string.IsNullOrWhiteSpace(key))
		{
			throw new Exception();
		}

		return Guid.NewGuid().ToString();
	}

	public List<Account> GetAllAccount(List<Account> accounts)
	{
		return accounts ?? new List<Account>();
	}

	public string GetApplicationName(int applicationId)
	{
		if (applicationId < 1)
		{
			return string.Empty;
		}
		return _externalService.GetApplicationName();
	}
}
