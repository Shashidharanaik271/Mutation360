
using Mutation360Team11.Enums;

namespace Mutation360Team11.Dtos;

public class AccountTypeAndDescriptionDetailsDto
{
	public string AccountDescription { get; set; } = null!;
	public AccountType? AccountType { get; set; }
}
